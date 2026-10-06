import os
import shutil
import hashlib
import sqlite3
from datetime import datetime



FILE_TYPES = {
    "Pictures": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
    ],

    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".xlsx",
        ".xls",
        ".ppt",
        ".pptx",
        ".csv",
        ".odt",
        ".rtf",
    ],

    "Videos": [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
    ],

    "Music": [
        ".mp3",
        ".wav",
        ".aac",
        ".flac",
        ".m4a",
        ".ogg",
    ],

    "Archives": [
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    ],

    "Code": [
        ".py",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".scss",
        ".php",
        ".sql",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".sh",
        ".bat",
    ],
}



USER_HOME = os.environ.get(
    "USERPROFILE",
    os.path.expanduser("~")
)


SYSTEM_FOLDERS = {
    "Pictures": os.path.join(USER_HOME, "Pictures"),
    "Documents": os.path.join(USER_HOME, "Documents"),
    "Videos": os.path.join(USER_HOME, "Videos"),
    "Music": os.path.join(USER_HOME, "Music"),
}




APP_DATA_FOLDER = os.path.join(
    os.environ.get(
        "LOCALAPPDATA",
        os.path.join(USER_HOME, "AppData", "Local")
    ),
    "AutomaticFileOrganizer"
)

os.makedirs(APP_DATA_FOLDER, exist_ok=True)

DATABASE_PATH = os.path.join(
    APP_DATA_FOLDER,
    "history.db"
)


def get_db_connection():
    """
    Open the local SQLite database.
    SQLite is built into Python, so no database server is needed.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """
    Create the required history tables if they don't exist.
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                source_folder TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                moved_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                duplicate_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY(operation_id)
                    REFERENCES operations(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


initialize_database()


def get_category(extension):
    """
    Return the category for a file extension.
    """

    extension = extension.lower()

    for category, extensions in FILE_TYPES.items():

        if extension in extensions:
            return category

    return "Others"


def get_destination(category, source_folder):
    """
    Get the correct destination.

    Pictures/Documents/Videos/Music:
        Existing Windows user folders.

    Archives/Code/Others:
        Created inside the selected source folder.
    """

    if category in SYSTEM_FOLDERS:
        return SYSTEM_FOLDERS[category]

    special_folder = os.path.join(
        source_folder,
        category
    )

    return special_folder

def get_file_hash(file_path):
    """
    Calculate SHA-256 hash of a file.
    Used for duplicate detection.
    """

    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(1024 * 1024)

            if not data:
                break

            hasher.update(data)

    return hasher.hexdigest()


def list_loose_files(folder_path):
    """
    Return files directly inside the selected folder.

    Files inside subfolders are ignored.
    """

    if not os.path.isdir(folder_path):
        return []

    files = []

    try:

        for name in os.listdir(folder_path):

            full_path = os.path.join(
                folder_path,
                name
            )

            if os.path.isfile(full_path):
                files.append(name)

    except (OSError, PermissionError):
        return []

    return sorted(files, key=str.lower)


def unique_destination(folder, filename):
    """
    Prevent overwriting an existing file.
    """

    os.makedirs(
        folder,
        exist_ok=True
    )

    destination = os.path.join(
        folder,
        filename
    )

    if not os.path.exists(destination):
        return destination

    base, extension = os.path.splitext(filename)

    counter = 1

    while True:

        new_name = f"{base}_{counter}{extension}"

        destination = os.path.join(
            folder,
            new_name
        )

        if not os.path.exists(destination):
            return destination

        counter += 1

def start_operation(source_folder, operation_type="organize"):
    """
    Create a history operation and return its ID.
    """

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        started_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO operations (
                operation_type,
                source_folder,
                started_at,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                operation_type,
                source_folder,
                started_at,
                "running",
            )
        )

        operation_id = cursor.lastrowid

        connection.commit()

        return operation_id

    finally:
        connection.close()


def record_file_move(
    operation_id,
    source_path,
    destination_path,
    file_name,
    category
):
    """
    Store one successful file move.
    """

    connection = get_db_connection()

    try:

        connection.execute(
            """
            INSERT INTO file_moves (
                operation_id,
                source_path,
                destination_path,
                file_name,
                category
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                operation_id,
                source_path,
                destination_path,
                file_name,
                category,
            )
        )

        connection.commit()

    finally:
        connection.close()


def finish_operation(
    operation_id,
    moved,
    skipped,
    duplicates,
    status="completed"
):
    """
    Finish a history operation.
    """

    connection = get_db_connection()

    try:

        completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

        connection.execute(
            """
            UPDATE operations
            SET
                completed_at = ?,
                moved_count = ?,
                skipped_count = ?,
                duplicate_count = ?,
                status = ?
            WHERE id = ?
            """,
            (
                completed_at,
                moved,
                skipped,
                duplicates,
                status,
                operation_id,
            )
        )

        connection.commit()

    finally:
        connection.close()

def organize_folder(
    folder_path,
    log_callback=print,
    dry_run=False
):
    """
    Organize files from folder_path.

    Existing Windows folders are used for:
        Pictures
        Documents
        Videos
        Music

    Folders are created inside the selected folder ONLY for:
        Archives
        Code
        Others

    Returns:
        {
            "moved": int,
            "skipped": int,
            "duplicates": int
        }
    """

    if not os.path.isdir(folder_path):

        log_callback(
            "❌ Error: That folder does not exist."
        )

        return {
            "moved": 0,
            "skipped": 0,
            "duplicates": 0,
        }


    moved_files = 0
    skipped_files = 0
    duplicate_files = 0

    file_hashes = {}

    operation_id = None

    if not dry_run:

        try:
            operation_id = start_operation(
                folder_path,
                "organize"
            )

        except Exception as error:

            log_callback(
                f"⚠ History database warning: {error}"
            )


    files = list_loose_files(folder_path)

    for filename in files:

        file_path = os.path.join(
            folder_path,
            filename
        )

        if filename.lower() in {
            "move_log.txt",
            "history.db",
        }:
            continue


        _, extension = os.path.splitext(
            filename
        )

        if not extension:

            skipped_files += 1

            log_callback(
                f"Skipped: {filename} → no file extension"
            )

            continue

        try:

            file_hash = get_file_hash(
                file_path
            )

        except (OSError, PermissionError) as error:

            skipped_files += 1

            log_callback(
                f"Skipped: {filename} → cannot read file ({error})"
            )

            continue
        if file_hash in file_hashes:

            duplicate_files += 1

            original = file_hashes[file_hash]

            log_callback(
                f"Duplicate: {filename} "
                f"→ same as {os.path.basename(original)}"
            )

            continue


        file_hashes[file_hash] = file_path



        category = get_category(
            extension
        )


        destination_folder = get_destination(
            category,
            folder_path
        )


        if category in SYSTEM_FOLDERS:

            # Pictures/Documents/Videos/Music
            # MUST already exist.
            if not os.path.isdir(
                destination_folder
            ):

                skipped_files += 1

                log_callback(
                    f"Skipped: {filename} → "
                    f"{category} folder not found"
                )

                continue

        else:

            
            if not dry_run:

                try:

                    os.makedirs(
                        destination_folder,
                        exist_ok=True
                    )

                except (OSError, PermissionError) as error:

                    skipped_files += 1

                    log_callback(
                        f"Skipped: {filename} → "
                        f"cannot create {category} folder ({error})"
                    )

                    continue


        try:

            destination_path = unique_destination(
                destination_folder,
                filename
            )

        except (OSError, PermissionError) as error:

            skipped_files += 1

            log_callback(
                f"Skipped: {filename} → "
                f"destination error ({error})"
            )

            continue


  
        if dry_run:

            log_callback(
                f"[PREVIEW] {filename} → {category}"
            )

            moved_files += 1

            continue


        

        try:

            shutil.move(
                file_path,
                destination_path
            )


            # Record in SQLite
            if operation_id is not None:

                try:

                    record_file_move(
                        operation_id,
                        file_path,
                        destination_path,
                        filename,
                        category
                    )

                except Exception as db_error:

                    log_callback(
                        f"⚠ History warning for "
                        f"{filename}: {db_error}"
                    )


            moved_files += 1

            
            log_callback(
                f"Moved: {filename} → {category}"
            )

        except (
            OSError,
            PermissionError,
            shutil.Error
        ) as error:

            skipped_files += 1

            log_callback(
                f"Error moving {filename}: {error}"
            )


   

    if not dry_run and operation_id is not None:

        try:

            finish_operation(
                operation_id,
                moved_files,
                skipped_files,
                duplicate_files,
                "completed"
            )

        except Exception as db_error:

            log_callback(
                f"⚠ Could not finish history record: {db_error}"
            )



    if dry_run:

        log_callback(
            "\n----- PREVIEW COMPLETE -----"
        )

        log_callback(
            f"Files that can be moved : {moved_files}"
        )

    else:

        log_callback(
            "\n----- ORGANIZATION COMPLETE -----"
        )

        log_callback(
            f"Files moved      : {moved_files}"
        )

    log_callback(
        f"Files skipped    : {skipped_files}"
    )

    log_callback(
        f"Duplicates found : {duplicate_files}"
    )


    return {
        "moved": moved_files,
        "skipped": skipped_files,
        "duplicates": duplicate_files,
    }

def find_duplicates(folder_path):
    """
    Find duplicate files directly inside the selected folder.

    Nothing is moved or deleted.
    """

    if not os.path.isdir(folder_path):
        return []


    hashes = {}

    for filename in list_loose_files(
        folder_path
    ):

        if filename.lower() in {
            "move_log.txt",
            "history.db",
        }:
            continue


        path = os.path.join(
            folder_path,
            filename
        )


        try:

            file_hash = get_file_hash(
                path
            )

        except (OSError, PermissionError):

            continue


        hashes.setdefault(
            file_hash,
            []
        ).append(path)


    return [
        group
        for group in hashes.values()
        if len(group) > 1
    ]


def delete_file(file_path):
    """
    Delete one selected duplicate file.
    """

    if not os.path.isfile(file_path):
        return False

    try:

        os.remove(file_path)
        return True

    except (
        OSError,
        PermissionError
    ):

        return False


def get_history(limit=100):
    """
    Return recent organization history.

    Each item contains:
        id
        operation_type
        source_folder
        started_at
        completed_at
        moved_count
        skipped_count
        duplicate_count
        status
    """

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM operations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


def get_operation_moves(operation_id):
    """
    Return all files moved during one operation.
    """

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM file_moves
            WHERE operation_id = ?
            ORDER BY id ASC
            """,
            (operation_id,)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


def undo_last(
    folder_path,
    log_callback=print
):
    """
    Undo the most recent completed organization operation
    for the selected source folder.

    Only files that were actually moved in that operation
    are restored.
    """

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM operations
            WHERE source_folder = ?
              AND operation_type = 'organize'
              AND status = 'completed'
              AND moved_count > 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (folder_path,)
        )

        operation = cursor.fetchone()

    finally:

        connection.close()


    if operation is None:

        log_callback(
            "Nothing to undo for this folder."
        )

        return 0


    operation_id = operation["id"]

    moves = get_operation_moves(
        operation_id
    )


    if not moves:

        log_callback(
            "Nothing to undo - no file moves recorded."
        )

        return 0


    restored = 0


    for move in reversed(moves):

        source = move["source_path"]
        destination = move["destination_path"]
        filename = move["file_name"]


        try:

            if not os.path.exists(
                destination
            ):

                log_callback(
                    f"Skipped: {filename} "
                    f"→ destination file is missing"
                )

                continue


            
            if os.path.exists(source):

                log_callback(
                    f"Skipped: {filename} "
                    f"→ original location already contains a file"
                )

                continue


            shutil.move(
                destination,
                source
            )

            restored += 1

            log_callback(
                f"Restored: {filename}"
            )

        except (
            OSError,
            PermissionError,
            shutil.Error
        ) as error:

            log_callback(
                f"Error restoring {filename}: {error}"
            )


    
    connection = get_db_connection()

    try:

        connection.execute(
            """
            UPDATE operations
            SET status = 'undone'
            WHERE id = ?
            """,
            (operation_id,)
        )

        connection.commit()

    finally:

        connection.close()


    log_callback(
        f"\nUndo complete! {restored} file(s) restored."
    )

    return restored



if __name__ == "__main__":

    target_folder = input(
        "Enter the folder path to organize: "
    ).strip()

    organize_folder(
        target_folder
    )
