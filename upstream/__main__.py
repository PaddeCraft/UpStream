from log4py.log4py import logger
from flask import (
    Flask,
    abort,
    request,
    render_template,
    redirect,
    Response,
    stream_with_context,
)
from werkzeug.utils import secure_filename
from upstream.sourceCodeFormats import formats as sourceCodeFormats
from upstream.__init__ import VERSION
from upstream.getFileIcon import getFileIcon
from datetime import datetime
from uuid import uuid1 as uuid
from operator import itemgetter
import os
import time
import json
import glob
import typer
import socket
import logging
import zipfile
import pathlib
import threading

log = logger(timeFormat="%H:%M:%S")
app = Flask("UpStream", root_path=pathlib.Path(__file__).parent.absolute())
ip = socket.gethostbyname(socket.gethostname())
basePath = "."
_showSizeForFolders = False

logging.getLogger("werkzeug").disabled = True

zippingProcesses = []


def getPath(path: str):
    p = path.replace("\\", "/")
    p = p + "/" if p[-1] != "/" else ""
    return os.path.join(basePath, path).replace("\\", "/").replace("~/", "")


def read_file_chunks(path):
    with open(path, "rb") as fd:
        while 1:
            buf = fd.read(8192)
            if buf:
                yield buf
            else:
                break


def humanbytes(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    # from https://stackoverflow.com/a/31631711
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return "{0} {1}".format(B, "Bytes" if 0 == B > 1 else "Byte")
    elif KB <= B < MB:
        return "{0:.2f} KB".format(B / KB)
    elif MB <= B < GB:
        return "{0:.2f} MB".format(B / MB)
    elif GB <= B < TB:
        return "{0:.2f} GB".format(B / GB)
    elif TB <= B:
        return "{0:.2f} TB".format(B / TB)


def breadcrumbGenerator(path):
    breadcrumbs = []
    for crumb in path.replace(basePath, "").split("/"):
        if not crumb == "":
            breadcrumbNames = []
            for x in breadcrumbs:
                breadcrumbNames.append(x["name"])
            isDir = os.path.isdir(
                os.path.join(basePath, "/".join(breadcrumbNames), crumb)
            )
            breadcrumbs.append(
                {
                    "name": crumb,
                    "type": "dir" if isDir else "file",
                    "link": "" + "/".join(breadcrumbNames) + "/" + crumb,
                }
            )
    return breadcrumbs


def getDirSize(pth):
    dirTreeSize = 0
    for path, _, files in os.walk(pth):
        for file in files:
            pth = os.path.join(path, file)
            try:
                dirTreeSize += os.path.getsize(pth)
            except:
                pass
    return dirTreeSize


def scanDir(dir) -> list:
    files = []
    for root, _, files in os.walk(dir):
        for file in files:
            yield os.path.join(root, file)



def zipFolder(path, files, processUUID):
    global zippingProcesses
    zippingProcesses.append({"uuid": processUUID, "path": path})
    with zipfile.ZipFile(
        os.path.join(basePath, "upstream-tmp", f"{processUUID}.zip"),
        "w",
    ) as zipf:
        for file in files:
            zipf.write(
                file,
                file.replace("\\", "/").replace(path, ""),
            )
    # https://stackoverflow.com/a/43049879
    zippingProcesses.pop(
        list(map(itemgetter("uuid"), zippingProcesses)).index(processUUID)
    )


@app.route("/")
def index():
    return redirect("/explore/~/")


@app.route("/explore/<path:path>")
def explore(path):
    pth = getPath(path)
    if os.path.isdir(pth):
        files = []
        for f in os.listdir(pth):
            isFile = os.path.isfile(os.path.join(pth, f))
            if not isFile and f == "upstream-tmp":
                pass
            else:
                files.append(
                    {
                        "name": f,
                        "size": humanbytes(os.path.getsize(os.path.join(pth, f)))
                        if isFile
                        else (
                            humanbytes(getDirSize(os.path.join(pth, f)))
                            if _showSizeForFolders
                            else "---"
                        ),
                        "date": datetime.utcfromtimestamp(
                            os.path.getmtime(os.path.join(pth, f))
                        ).strftime("%d.%m.%Y %H:%M:%S"),
                        "link": path.replace("\\", "/") + f"/{f}",
                        "icon": "folder"
                        if not isFile
                        else getFileIcon(pathlib.Path(f).suffix.lower()[1:]),
                        "isFile": isFile,
                    }
                )
        breadcrumbs = breadcrumbGenerator(pth)
        title = path.replace("\\", "/").split("/")
        for i in list(reversed(title)):
            if not i == "":
                title = i
                break
        return render_template(
            "explore.html",
            files=sorted(files, key=lambda item: item["isFile"]),
            breadcrumbs=breadcrumbs,
            title=title,
            currentPath=path.replace("\\", "/"),
        )
    else:
        pth = getPath(path)
        ext = pathlib.Path(pth).suffix.lower()[1:]
        dwnLoadPath = "/download/" + path
        if ext == "pdf":
            return render_template(
                "preview/pdf.html",
                file=dwnLoadPath,
                breadcrumbs=breadcrumbGenerator(pth),
            )
        elif ext in ["jpg", "jpeg", "png", "gif"]:
            return render_template(
                "preview/image.html",
                file=dwnLoadPath,
                breadcrumbs=breadcrumbGenerator(pth),
            )
        elif ext in sourceCodeFormats:
            return render_template(
                "preview/code.html",
                file=dwnLoadPath,
                breadcrumbs=breadcrumbGenerator(pth),
            )
        else:
            return redirect(dwnLoadPath)



@app.route("/download/<path:path>")
def download(path):
    global zippingProcesses
    pth = getPath(path)
    log.info(f"New download from path {pth}")
    if os.path.isfile(pth):
        log.info(f"Sending single file")
        return Response(
            stream_with_context(read_file_chunks(pth)),
            headers={
                "Content-Disposition": f'attachment; filename={pth.split("/")[-1]}',
            },
        )
    else:
        filesToZip = []
        requestedFileStr = request.args.get("files")
        if requestedFileStr == "*":
            filesToZip = [x for x in scanDir(pth)]
        else:
            elements = requestedFileStr.split("||")
            for element in elements:
                if os.path.isfile(os.path.join(pth, element)):
                    filesToZip.append(os.path.join(pth, element))
                else:
                    for file in scanDir(os.path.join(pth, element)):
                        filesToZip.append(file)
        zipProcessUUID = str(uuid())
        threading.Thread(args=(pth, filesToZip, zipProcessUUID), target=zipFolder).start()
        log.info(f"Zipping {len(filesToZip)} files")
        log.info(f"Zipping process UUID: {zipProcessUUID}")
        print("")
        time.sleep(1)
        return render_template("waitForZip.html", processUUID=zipProcessUUID, path=pth)


@app.route("/upload/<path:path>", methods=["POST"])
def upload(path):
    if 'file' not in request.files:
        return abort(400)
    file = request.files['file']
    if file.filename == '':
        return redirect(f"/explore/{path}")
    filename = secure_filename(file.filename)
    fp = os.path.join(getPath(path), filename)
    while os.path.exists(fp):
        fp = fp + ".removeme"
    file.save(fp)
    return redirect(f"/explore/{path}")


@app.route("/api/isProcessing/<_uuid>")
def isProcessing(_uuid):
    global zippingProcesses
    isStillProcessing = True
    maxSize = 0
    size = 0
    try:
        # https://stackoverflow.com/a/43049879
        dictForUUID = zippingProcesses[
            list(map(itemgetter("uuid"), zippingProcesses)).index(_uuid)
        ]
        maxSize = getDirSize(dictForUUID["path"])
        size = os.path.getsize(
            os.path.join(basePath, "upstream-tmp", f"{_uuid}.zip")
        ),
    except ValueError:
        isStillProcessing = False
    
    return json.dumps(
        {
            "isProcessing": isStillProcessing,
            "currentSize": size, 
            "maxSize": maxSize,
        }
    )


def main(port: int = 55555, directory: str = ".", folderSizeDisplay: bool = False, host: str = "0.0.0.0"):
    global basePath
    global _showSizeForFolders
    _showSizeForFolders = folderSizeDisplay
    log.info(f"UpStream {VERSION}")
    basePath = os.path.abspath(directory).replace("\\", "/")
    if not os.path.isdir(basePath):
        log.error(f"{basePath} is not a directory")
        exit(1)
    elif os.access(basePath, os.R_OK) and os.access(basePath, os.W_OK):
        os.makedirs(os.path.join(basePath, "upstream-tmp"), exist_ok=True)
    else:
        log.error(f"{basePath} is not R/W permitted.")
        exit(1)
    with app.app_context():
        log.success(f"Running on {ip}:{port}")
    try:
        print("")
        app.run(host=host, port=port, use_reloader=False)
    except:
        try:
            log.info("Removing temporary files, please wait...")
            os.rmdir(os.path.join(basePath, "upstream-tmp"))
            log.success("Done")
            exit(0)
        except:
            log.error(
                "Failed to remove temporary files at "
                + os.path.join(basePath, "upstream-tmp")
                + ". You need to do this mannually."
            )
            exit(1)


if __name__ == "__main__":
    typer.run(main)
