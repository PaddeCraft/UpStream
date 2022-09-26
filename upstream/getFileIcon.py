from upstream.sourceCodeFormats import formats as sourceCodeFormats

def getFileIcon(ext):
    if ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
        return "image"
    elif ext in ["mp3", "wav", "flac", "ogg"]:
        return "music_note"
    elif ext in ["mp4", "mkv", "avi", "webm"]:
        return "movie"
    elif ext in ["exe", "msi", "apk", "dmg"]:
        return "file_upload"
    elif ext in ["txt", "doc", "docx", "pdf", "odt", "rtf", "tex", "texi", "texinfo"]:
        return "description"
    elif ext in ["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "lz", "lzma", "lzo", "zst"]:
        return "archive"
    elif ext in ["iso", "img", "bin", "cue", "toast", "vcd", "cdr", "dvd", "bin", "bak", "bup"]:
        return "storage"
    elif ext in sourceCodeFormats: # ["html", "css", "js", "py", "cpp", "c", "csharp", "java", "cs", "json", "xml", "yml", "yaml"]:
        return "code"
    else:
        return "insert_drive_file"