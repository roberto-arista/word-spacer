import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttGlyphSet import _TTGlyphSetCFF, _TTGlyphSetGlyf, _TTGlyphSetVARC
from ufo2svg.svgPathPen import SVGPathPen

from app.config import settings

fontPath = settings.STATIC_DIR / "fonts/IntelOneMono-Regular.otf"


def defaultFeatureToState() -> dict[str, bool]:
    return {"kern": True, "locl": True, "liga": True, "calt": True}


Glyf = _TTGlyphSetVARC | _TTGlyphSetCFF | _TTGlyphSetGlyf
UNITS_PER_EM_DEFAULT = 1000


@dataclass
class GlyphRecord:

    glyph: Glyf
    xPlacement: int
    yPlacement: int
    xAdvance: int
    yAdvance: int


@dataclass
class Shaper:

    binaryPath: Path
    featureToState: dict[str, bool] = field(default_factory=defaultFeatureToState)
    glyphSet: dict = field(default_factory=dict)

    def __post_init__(self):
        self.ttFont = TTFont(self.binaryPath)
        self.glyphSet = cast(dict, self.ttFont.getGlyphSet())
        data = io.BytesIO()
        self.ttFont.save(data)
        face = hb.Face(data.getvalue())  # type: ignore
        self.hbFont = hb.Font(face)  # type: ignore

    @property
    def unitsPerEm(self) -> int:
        return self.ttFont["head"].unitsPerEm  # type: ignore

    @property
    def ascender(self) -> int:
        return self.ttFont["OS/2"].sTypoAscender  # type: ignore

    @property
    def descender(self) -> int:
        return self.ttFont["OS/2"].sTypoDescender  # type: ignore

    def resetFeatures(self):
        self.featureToState = defaultFeatureToState()

    def process(
        self,
        text: str,
        script: str | None = None,
        langSys: str | None = None,
        rightToLeft: bool = False,
    ) -> list[GlyphRecord]:
        buf = hb.Buffer()  # type: ignore
        buf.add_str(text)
        buf.guess_segment_properties()

        buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS  # type: ignore

        if script:
            buf.set_script_from_ot_tag(script)
        if langSys:
            buf.set_language_from_ot_tag(langSys)
        buf.direction = "rtl" if rightToLeft else "ltr"

        hb.shape(self.hbFont, buf, self.featureToState)  # type: ignore

        infos = buf.glyph_infos
        positions = buf.glyph_positions

        glyphRecords = []
        for info, pos in zip(infos, positions):
            index = info.codepoint
            glyphName = self.ttFont.getGlyphName(index)
            glyphRecords.append(
                GlyphRecord(
                    glyph=self.glyphSet[glyphName],
                    xPlacement=pos.x_offset,
                    yPlacement=pos.y_offset,
                    xAdvance=pos.x_advance,
                    yAdvance=pos.y_advance,
                )
            )
        return glyphRecords

    def convertToSVG(self, glyphRecords: list[GlyphRecord]) -> str:
        if not glyphRecords:
            return ""

        paths = []
        xRunAdvance = 0
        yRunAdvance = 0

        for glyphRecord in glyphRecords:

            svgPen = SVGPathPen(self.glyphSet)
            glyphRecord.glyph.draw(svgPen)  # type: ignore

            # translate()
            paths.append(
                f"""<path 
                    transform="
                        scale(1 -1)
                        scale(1 1)
                        translate({xRunAdvance} {-self.ascender-self.descender})"
                    d="{svgPen.getCommands()}"
                    fill="black"/>
                """
            )
            xRunAdvance += glyphRecord.xAdvance
            yRunAdvance += glyphRecord.yAdvance

        # width="{xRunAdvance}" height="{self.unitsPerEm}"
        return f"""\
        <svg viewBox="0 0 {xRunAdvance} {self.unitsPerEm}">
            {''.join(paths)}
        </svg>
        """


def typeset(word: str) -> str:
    shaper = Shaper(fontPath)
    records = shaper.process(word)
    return shaper.convertToSVG(records)


if __name__ == "__main__":
    from icecream import ic

    shaper = Shaper(fontPath)
    records = shaper.process("ı́")
    ic([i.glyph.name for i in records])  # type: ignore
    ic(records)
