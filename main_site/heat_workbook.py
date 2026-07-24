from collections import defaultdict
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


PRINTABLE_HEAT_HEADERS = [
    "Position",
    "Bib",
    "First Name",
    "Last Name",
    "Gender",
    "Seed",
    "Hometown",
    "Sponsor",
    "Unofficial Time",
    "Official Time",
    "Place",
]


def build_printable_heat_workbook(assignments, year):
    workbook = _HeatWorkbook(year, assignments)
    return workbook.to_bytes()


class _HeatWorkbook:
    def __init__(self, year, assignments):
        self.year = year
        self.assignments_by_heat = _group_assignments_by_heat(assignments)
        self.merge_ranges = []
        self.page_break_rows = []
        self.rows = self._build_rows()

    def to_bytes(self):
        output = BytesIO()

        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", _content_types_xml())
            archive.writestr("_rels/.rels", _root_rels_xml())
            archive.writestr("xl/workbook.xml", _workbook_xml())
            archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
            archive.writestr("xl/styles.xml", _styles_xml())
            archive.writestr("xl/worksheets/sheet1.xml", self._worksheet_xml())
            archive.writestr("docProps/core.xml", _core_properties_xml())
            archive.writestr("docProps/app.xml", _app_properties_xml())

        return output.getvalue()

    def _build_rows(self):
        rows = [
            _row(
                [
                    _cell(f"Guinea Pig Mile {self.year} Heats", style=1),
                    *[_cell("", style=1) for _ in range(len(PRINTABLE_HEAT_HEADERS) - 1)],
                ],
                height=30,
            ),
            _row(
                [
                    _cell(
                        "Print-ready heat sheets. Championship heats follow the co-ed heats.",
                        style=2,
                    ),
                    *[_cell("", style=2) for _ in range(len(PRINTABLE_HEAT_HEADERS) - 1)],
                ],
                height=22,
            ),
            _row([_cell("") for _ in PRINTABLE_HEAT_HEADERS], height=10),
        ]
        self.merge_ranges.extend(["A1:K1", "A2:K2"])

        for heat_index, heat in enumerate(self.assignments_by_heat):
            if heat_index:
                self.page_break_rows.append(len(rows) + 1)
                rows.append(_row([_cell("") for _ in PRINTABLE_HEAT_HEADERS], height=8))

            title_row = len(rows) + 1
            rows.append(
                _row(
                    [
                        _cell(
                            f"{heat['heat_name']} ({heat['heat_type']}) - {len(heat['assignments'])} runners",
                            style=3,
                        ),
                        *[_cell("", style=3) for _ in range(len(PRINTABLE_HEAT_HEADERS) - 1)],
                    ],
                    height=25,
                )
            )
            self.merge_ranges.append(f"A{title_row}:K{title_row}")

            rows.append(
                _row(
                    [_cell(header, style=4) for header in PRINTABLE_HEAT_HEADERS],
                    height=20,
                )
            )

            for assignment in heat["assignments"]:
                registrant = assignment.registrant
                rows.append(
                    _row(
                        [
                            _cell(assignment.position, style=5),
                            _cell("", style=5),
                            _cell(registrant.first_name, style=5),
                            _cell(registrant.last_name, style=5),
                            _cell(registrant.gender, style=5),
                            _cell(registrant.seed_time, style=5),
                            _cell(registrant.hometown or "", style=5),
                            _cell(registrant.sponsor or "", style=5),
                            _cell("", style=5),
                            _cell("", style=5),
                            _cell("", style=5),
                        ],
                        height=22,
                    )
                )

        return rows

    def _worksheet_xml(self):
        return "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
                '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>',
                '<dimension ref="A1:K{}"/>'.format(len(self.rows)),
                "<sheetViews><sheetView workbookViewId=\"0\" showGridLines=\"0\"/></sheetViews>",
                "<sheetFormatPr defaultRowHeight=\"18\"/>",
                _columns_xml(),
                _sheet_data_xml(self.rows),
                _merge_cells_xml(self.merge_ranges),
                _row_breaks_xml(self.page_break_rows),
                '<pageMargins left="0.25" right="0.25" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>',
                '<pageSetup paperSize="1" orientation="landscape" fitToWidth="1" fitToHeight="0"/>',
                '<headerFooter><oddHeader>&amp;CGuinea Pig Mile Heats</oddHeader><oddFooter>&amp;RPage &amp;P of &amp;N</oddFooter></headerFooter>',
                "</worksheet>",
            ]
        )


def _group_assignments_by_heat(assignments):
    grouped = defaultdict(list)
    heat_names = {}
    heat_types = {}

    for assignment in assignments:
        grouped[assignment.heat_number].append(assignment)
        heat_names[assignment.heat_number] = assignment.heat_name
        heat_types[assignment.heat_number] = assignment.heat_type

    return [
        {
            "heat_number": heat_number,
            "heat_name": heat_names[heat_number],
            "heat_type": heat_types[heat_number],
            "assignments": sorted(
                grouped[heat_number],
                key=lambda assignment: assignment.position,
            ),
        }
        for heat_number in sorted(grouped)
    ]


def _row(cells, height=None):
    return {"cells": cells, "height": height}


def _cell(value, style=0):
    return {"value": value, "style": style}


def _sheet_data_xml(rows):
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        height_attrs = ""
        if row["height"] is not None:
            height_attrs = f' ht="{row["height"]}" customHeight="1"'

        cells = [
            _cell_xml(row_index, column_index, cell)
            for column_index, cell in enumerate(row["cells"], start=1)
        ]
        row_xml.append(f'<row r="{row_index}"{height_attrs}>{"".join(cells)}</row>')

    return f"<sheetData>{''.join(row_xml)}</sheetData>"


def _cell_xml(row_index, column_index, cell):
    coordinate = f"{_column_name(column_index)}{row_index}"
    style = cell["style"]
    value = cell["value"]

    if value is None:
        value = ""

    if isinstance(value, int):
        return f'<c r="{coordinate}" s="{style}"><v>{value}</v></c>'

    return (
        f'<c r="{coordinate}" s="{style}" t="inlineStr">'
        f"<is><t>{escape(str(value))}</t></is>"
        "</c>"
    )


def _column_name(column_index):
    name = ""
    while column_index:
        column_index, remainder = divmod(column_index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _columns_xml():
    widths = [10, 10, 15, 16, 12, 10, 22, 22, 16, 14, 10]
    columns = [
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(widths, start=1)
    ]
    return f"<cols>{''.join(columns)}</cols>"


def _merge_cells_xml(merge_ranges):
    merge_cells = "".join(f'<mergeCell ref="{merge_range}"/>' for merge_range in merge_ranges)
    return f'<mergeCells count="{len(merge_ranges)}">{merge_cells}</mergeCells>'


def _row_breaks_xml(page_break_rows):
    if not page_break_rows:
        return ""

    breaks = "".join(
        f'<brk id="{row_number}" max="16383" man="1"/>' for row_number in page_break_rows
    )
    return f'<rowBreaks count="{len(page_break_rows)}" manualBreakCount="{len(page_break_rows)}">{breaks}</rowBreaks>'


def _content_types_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _root_rels_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _workbook_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Printable Heats" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""


def _workbook_rels_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def _styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="5">
    <font><sz val="11"/><color rgb="FF111827"/><name val="Aptos"/></font>
    <font><b/><sz val="18"/><color rgb="FFFFFFFF"/><name val="Aptos Display"/></font>
    <font><i/><sz val="11"/><color rgb="FF374151"/><name val="Aptos"/></font>
    <font><b/><sz val="14"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font>
  </fonts>
  <fills count="5">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F2937"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE5E7EB"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFB91C1C"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="3">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color rgb="FFD1D5DB"/></left><right style="thin"><color rgb="FFD1D5DB"/></right><top style="thin"><color rgb="FFD1D5DB"/></top><bottom style="thin"><color rgb="FFD1D5DB"/></bottom><diagonal/></border>
    <border><bottom style="medium"><color rgb="FF111827"/></bottom><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFill="1" applyFont="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="4" borderId="0" xfId="0" applyFill="1" applyFont="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="4" fillId="2" borderId="1" xfId="0" applyFill="1" applyFont="1" applyBorder="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment vertical="center" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _core_properties_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Guinea Pig Mile Printable Heats</dc:title>
  <dc:creator>Guinea Pig Mile</dc:creator>
</cp:coreProperties>"""


def _app_properties_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Guinea Pig Mile</Application>
</Properties>"""
