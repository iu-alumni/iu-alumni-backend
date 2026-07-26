"""Tests for uploading the allowed-emails list.

This list gates who may register at all, so the route is admin-only and must
reject anything that isn't a spreadsheet before handing bytes to the parser.
"""

import io
import uuid

from fastapi import HTTPException, UploadFile
import pytest

from app.api.routes.admin.upload_allowed_emails import upload_allowed_emails
from app.models.users import Admin, Alumni


def _admin() -> Admin:
    return Admin(id=str(uuid.uuid4()), email="admin@innopolis.university")


def _alumni() -> Alumni:
    return Alumni(
        id=str(uuid.uuid4()),
        email="ada@innopolis.university",
        hashed_password="hash",
        first_name="Ada",
        last_name="Lovelace",
        graduation_year="2024",
    )


def _upload(filename: str, content: bytes = b"binary-xlsx") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


@pytest.mark.asyncio
async def test_non_admin_cannot_upload(db_session, mocker):
    process = mocker.patch(
        "app.api.routes.admin.upload_allowed_emails.process_excel_file"
    )

    with pytest.raises(HTTPException) as exc:
        await upload_allowed_emails(
            file=_upload("emails.xlsx"), current_user=_alumni(), db=db_session
        )

    assert exc.value.status_code == 403
    # Rejected before the file is even parsed.
    process.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["emails.csv", "emails.txt", "payload.exe", "emails"])
async def test_rejects_non_excel_files(db_session, mocker, filename):
    process = mocker.patch(
        "app.api.routes.admin.upload_allowed_emails.process_excel_file"
    )

    with pytest.raises(HTTPException) as exc:
        await upload_allowed_emails(
            file=_upload(filename), current_user=_admin(), db=db_session
        )

    assert exc.value.status_code == 400
    process.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["emails.xlsx", "emails.xls"])
async def test_accepts_excel_extensions(db_session, mocker, filename):
    mocker.patch(
        "app.api.routes.admin.upload_allowed_emails.process_excel_file",
        return_value={"success": True, "message": "3 emails imported"},
    )

    result = await upload_allowed_emails(
        file=_upload(filename), current_user=_admin(), db=db_session
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_passes_file_bytes_to_the_parser(db_session, mocker):
    process = mocker.patch(
        "app.api.routes.admin.upload_allowed_emails.process_excel_file",
        return_value={"success": True, "message": "ok"},
    )

    await upload_allowed_emails(
        file=_upload("emails.xlsx", b"spreadsheet-bytes"),
        current_user=_admin(),
        db=db_session,
    )

    assert process.call_args.args[1] == b"spreadsheet-bytes"


@pytest.mark.asyncio
async def test_parser_failure_becomes_400(db_session, mocker):
    mocker.patch(
        "app.api.routes.admin.upload_allowed_emails.process_excel_file",
        return_value={"success": False, "message": "First column must contain emails"},
    )

    with pytest.raises(HTTPException) as exc:
        await upload_allowed_emails(
            file=_upload("emails.xlsx"), current_user=_admin(), db=db_session
        )

    assert exc.value.status_code == 400
    # The parser's reason is surfaced so the admin can fix the sheet.
    assert exc.value.detail == "First column must contain emails"
