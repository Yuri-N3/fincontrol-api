from datetime import date

from database import db


class ValidationError(ValueError):
    pass


def parse_date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value) if value else None
    except (TypeError, ValueError) as exc:
        raise ValidationError("Data invalida. Use o formato AAAA-MM-DD.") from exc


def validate_payload(payload, required_fields=None, numeric_fields=None):
    required_fields = required_fields or ()
    numeric_fields = numeric_fields or ()
    missing = [field for field in required_fields if payload.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"Campos obrigatorios ausentes: {', '.join(missing)}")
    for field in numeric_fields:
        if field in payload and payload[field] not in (None, ""):
            try:
                payload[field] = float(payload[field])
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"Campo numerico invalido: {field}") from exc
    return payload


def apply_payload(model, payload, date_fields=None, allowed_fields=None):
    date_fields = date_fields or set()
    fields = allowed_fields or payload.keys()
    for field in fields:
        if field not in payload:
            continue
        value = payload[field]
        if field in date_fields and value:
            value = parse_date(value)
        setattr(model, field, value)
    return model


def save(model):
    db.session.add(model)
    db.session.commit()
    return model


def delete(model):
    db.session.delete(model)
    db.session.commit()
