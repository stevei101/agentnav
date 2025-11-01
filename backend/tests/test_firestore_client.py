import os
import time
from google.cloud import firestore

from services.firestore_client import get_client


def test_get_client_returns_firestore_client(monkeypatch):
    # Ensure emulator env is set for tests (CI sets FIRESTORE_EMULATOR_HOST)
    emulator = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8081")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", emulator)
    monkeypatch.setenv("FIRESTORE_PROJECT_ID", "agentnav-dev")

    client = get_client()
    assert isinstance(client, firestore.Client)


def test_can_write_and_read_document(monkeypatch):
    # Integration-style test against the emulator
    emulator = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8081")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", emulator)
    monkeypatch.setenv("FIRESTORE_PROJECT_ID", "agentnav-dev")

    db = get_client()
    coll = db.collection("test_collection")
    doc_ref = coll.document("test_doc")
    payload = {"hello": "world"}
    doc_ref.set(payload)

    # Small delay for emulator consistency
    time.sleep(0.2)

    read = doc_ref.get()
    assert read.exists
    assert read.to_dict().get("hello") == "world"
