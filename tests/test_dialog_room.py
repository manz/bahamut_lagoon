"""
Test rooms for the dialogue VWF: a French text laid out and encoded as the build does it (utils.dump_rooms), shown by
a script injected into room 0 (tests/test_room_opcodes.Room), then the screen compared with its golden. Each case is
one thing the script's texts rely on, without hunting for the scene that has it.
"""

from pathlib import Path

from katsuji.script import Table

from tests.conftest import Console
from tests.test_room_opcodes import Room
from utils.dialog_layout import CENTER, LEFT, default_layout
from utils.name_tables import add_name_references, read_names
from utils.vm.room_asm import op

TABLE = Path("text/table/mz.tbl")
NAMES = Path("text/fr/names.xml")
TYPED = 240  # frames for the typewriter to finish a full window


def encoded(text: str, align: str = LEFT) -> bytes:
    """`text` as the build stores it: reflowed to a 3-line window, names as their record references."""
    laid_out = default_layout().reflow(text, page_lines=3, align=align)
    table = add_name_references(Table(str(TABLE)), read_names(NAMES))
    return bytes(table.to_bytes(laid_out.replace(" ", r"\s")))


def show(console: Console, text: bytes, style: int = 1, row: int = 0x14) -> None:
    """Open a window (style 0: frameless) at `row` and print `text` in it, left waiting for a key."""
    room = Room(console)
    room.run(
        [
            op("set_window_position", row, 6),
            op("open_window", style),
            op("display_text", "text"),
            op("close_window"),
            op("exit"),
            "text",
            text,
        ],
        frames=TYPED,
    )


def test_a_speech_wraps_to_the_window(console: Console) -> None:
    show(
        console,
        encoded(
            "Matelite: Princesse Yoyo, j'ai juré de vous protéger, et je tiendrai parole jusqu'au bout, "
            "même si le ciel tout entier devait tomber sur Kana ![end]"
        ),
    )
    assert console.matches_golden("dialog-room-wrap")


def test_names_print_from_their_records(console: Console) -> None:
    show(console, encoded("Bikebake: Byuu ! Salamand a encore mangé tous les champignons de Yoyo ![end]"))
    assert console.matches_golden("dialog-room-names")


def test_quotes_and_accents(console: Console) -> None:
    show(console, encoded("Truth: Il a dit ``Écoute'' à Ève... Ça, c'est un cœur à l'épreuve, où qu'il aille ![end]"))
    assert console.matches_golden("dialog-room-accents")


def test_a_frameless_text_is_centred(console: Console) -> None:
    show(console, encoded("Chapitre 9\n-Mahal, le continent des miracles-[end]", align=CENTER), style=0, row=0x09)
    assert console.matches_golden("dialog-room-centred")


def test_punctuation(console: Console) -> None:
    show(console, encoded("Bikebake: Champignons (ma part : 1/10)... Au secouuuurs~ Mon œil, sœur ![end]"))
    assert console.matches_golden("dialog-room-punctuation")
