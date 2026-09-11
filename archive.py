import io
import zipfile


def create_zip(files: dict[str, str]) -> bytes:

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for path, content in files.items():

            archive.writestr(
                path,
                content
            )

    return buffer.getvalue()