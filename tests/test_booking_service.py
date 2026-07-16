from datetime import date, time, timedelta

import pytest

from booking_service import BookingError, BookingService


def details(**overrides):
    values = dict(
        candidate_name="Test Candidate", room="upper room", day=date.today(), start=time(14, 0),
        duration_minutes=90, implementation_partner="Partner", client="Client", role="AI Engineer",
    )
    values.update(overrides)
    return values


def test_aliases(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    assert service.normalize_room("top floor") == "Room 1"
    assert service.normalize_room("hall") == "Room 2"


def test_overlap_is_rejected(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    service.create_booking(**details())
    with pytest.raises(BookingError, match="already booked"):
        service.create_booking(**details(candidate_name="Second", start=time(15, 0)))


def test_adjacent_booking_is_allowed(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    service.create_booking(**details())
    booking_id, _ = service.create_booking(**details(candidate_name="Second", start=time(15, 30)))
    assert booking_id


def test_other_room_is_allowed(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    service.create_booking(**details())
    booking_id, _ = service.create_booking(**details(candidate_name="Second", room="hall"))
    assert booking_id


def test_date_window(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    with pytest.raises(BookingError, match="next four days"):
        service.create_booking(**details(day=date.today() + timedelta(days=5)))


def test_cancel_frees_slot(tmp_path):
    service = BookingService(tmp_path / "bookings.xlsx")
    booking_id, _ = service.create_booking(**details())
    assert service.cancel_booking(booking_id)
    new_id, _ = service.create_booking(**details(candidate_name="Second"))
    assert new_id
