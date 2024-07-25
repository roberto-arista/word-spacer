import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttGlyphSet import _TTGlyphSetCFF, _TTGlyphSetGlyf, _TTGlyphSetVARC
from ufo2svg.svgPathPen import SVGPathPen

from app.config import settings

FONT_PATH = settings.STATIC_DIR / "fonts/IntelOneMono-Regular.otf"


def default_feature_to_state() -> dict[str, bool]:
    return {"kern": True, "locl": True, "liga": True, "calt": True}


Glyf = _TTGlyphSetVARC | _TTGlyphSetCFF | _TTGlyphSetGlyf
UNITS_PER_EM_DEFAULT = 1000


@dataclass
class GlyphRecord:

    glyph: Glyf
    x_placement: int
    y_placement: int
    x_advance: int
    y_advance: int


@dataclass
class Shaper:

    binary_path: Path
    feature_to_state: dict[str, bool] = field(default_factory=default_feature_to_state)
    glyph_set: dict = field(default_factory=dict)

    def __post_init__(self):
        self.tt_font = TTFont(self.binary_path)
        self.glyph_set = cast(dict, self.tt_font.getGlyphSet())
        data = io.BytesIO()
        self.tt_font.save(data)
        face = hb.Face(data.getvalue())  # type: ignore
        self.hb_font = hb.Font(face)  # type: ignore

    @property
    def units_per_em(self) -> int:
        return self.tt_font["head"].unitsPerEm  # type: ignore

    @property
    def ascender(self) -> int:
        return self.tt_font["OS/2"].sTypoAscender  # type: ignore

    @property
    def descender(self) -> int:
        return self.tt_font["OS/2"].sTypoDescender  # type: ignore

    def reset_features(self):
        self.feature_to_state = default_feature_to_state()

    def process(
        self,
        text: str,
        script: str | None = None,
        lang_sys: str | None = None,
        right_to_left: bool = False,
    ) -> list[GlyphRecord]:
        buf = hb.Buffer()  # type: ignore
        buf.add_str(text)
        buf.guess_segment_properties()

        buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS  # type: ignore

        if script:
            buf.set_script_from_ot_tag(script)
        if lang_sys:
            buf.set_language_from_ot_tag(lang_sys)
        buf.direction = "rtl" if right_to_left else "ltr"

        hb.shape(self.hb_font, buf, self.feature_to_state)  # type: ignore

        infos = buf.glyph_infos
        positions = buf.glyph_positions

        glyph_records = []
        for info, pos in zip(infos, positions):
            index = info.codepoint
            glyph_name = self.tt_font.getGlyphName(index)
            glyph_records.append(
                GlyphRecord(
                    glyph=self.glyph_set[glyph_name],
                    x_placement=pos.x_offset,
                    y_placement=pos.y_offset,
                    x_advance=pos.x_advance,
                    y_advance=pos.y_advance,
                )
            )
        return glyph_records

    def convert_to_svg(self, glyph_records: list[GlyphRecord]) -> str:
        if not glyph_records:
            return ""

        paths = []
        x_run_advance = 0
        y_run_advance = 0

        for glyph_record in glyph_records:

            svgPen = SVGPathPen(self.glyph_set)
            glyph_record.glyph.draw(svgPen)  # type: ignore

            # translate()
            paths.append(
                f"""<path 
                    transform="
                        scale(1 -1)
                        scale(1 1)
                        translate({x_run_advance} {-self.ascender-self.descender})"
                    d="{svgPen.getCommands()}"
                    fill="black"/>
                """
            )
            x_run_advance += glyph_record.x_advance
            y_run_advance += glyph_record.y_advance

        return f"""\
        <svg viewBox="0 0 {x_run_advance} {self.units_per_em}">
            {''.join(paths)}
        </svg>
        """


def typeset(word: str) -> str:
    shaper = Shaper(FONT_PATH)
    records = shaper.process(word)
    return shaper.convert_to_svg(records)


if __name__ == "__main__":
    from icecream import ic

    shaper = Shaper(FONT_PATH)
    records = shaper.process("ı́")
    ic([i.glyph.name for i in records])  # type: ignore
    ic(records)
