from pathlib import Path
import csv
from docx import Document
from docx.shared import Inches, Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "Group_2_Project_Report_Revised.docx"
GREEN = "112E81"
SOURCES = ["config.py", "simulation.py", "theory.py", "experiments.py",
           "plots.py", "draw_diagram.py", "main.py"]


def read_csv(name):
    """Read one project CSV as a list of row dictionaries."""
    with (ROOT / "outputs" / (name + ".csv")).open(
            encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def shade(cell, color):
    """Apply a solid fill to a table cell."""
    properties = cell._tc.get_or_add_tcPr()
    fill = OxmlElement("w:shd")
    fill.set(qn("w:fill"), color)
    properties.append(fill)


def set_font(style, name, size, color=None, bold=None):
    """Set a Word style font consistently across script alphabets."""
    style.font.name = name
    style.font.size = Pt(size)
    if color:
        style.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        style.font.bold = bold
    rpr = style._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn("w:" + key), name)


def set_run(run, name="Times New Roman", size=11, color=None, bold=None):
    """Set explicit font properties on one text run."""
    run.font.name = name
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn("w:" + key), name)


def set_run_family(run):
    """Set a text run's font family without changing its inherited size."""
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn("w:" + key), "Times New Roman")


def keep_row(row):
    """Prevent a table row from splitting across pages."""
    properties = row._tr.get_or_add_trPr()
    properties.append(OxmlElement("w:cantSplit"))


def set_cell_text(cell, text, header=False, align=None):
    """Write compact, consistently styled text into a table cell."""
    if align is None and str(text)[:1].isdigit():
        align = WD_ALIGN_PARAGRAPH.RIGHT
    cell.text = str(text)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(0)
        if align is not None:
            paragraph.alignment = align
        for run in paragraph.runs:
            set_run(run, size=10,
                    color="FFFFFF" if header else "000000",
                    bold=header)


def add_table(doc, headers, rows, aligns=None):
    """Create a styled, non-splitting table and repeat its header."""
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = True
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "bottom", "left", "right", "insideH", "insideV"):
        edge = OxmlElement("w:" + side)
        for key, value in (("val", "single"), ("sz", "4"), ("color", "C7CBC4")):
            edge.set(qn("w:" + key), value)
        borders.append(edge)
    table._tbl.tblPr.append(borders)
    for index, label in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], label, True,
                      aligns[index] if aligns else None)
        shade(table.rows[0].cells[index], GREEN)
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    table.rows[0]._tr.get_or_add_trPr().append(repeat)
    keep_row(table.rows[0])
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            set_cell_text(cells[index], value, False,
                          aligns[index] if aligns else None)
        keep_row(table.rows[-1])
    return table


def add_caption(doc, label, text, above=False):
    """Add a numbered table or figure caption in the accent color."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = above
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(label + " ")
    set_run(run, size=10, color=GREEN, bold=True)
    run = paragraph.add_run(text)
    set_run(run, size=10)
    return paragraph


def add_figure(doc, filename, number, caption, width=6):
    """Insert a project figure followed by its numbered caption."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(ROOT / "outputs" / "figures" / filename),
                                    width=Inches(width))
    add_caption(doc, "Figure " + str(number) + ".", caption)


def add_paragraph(doc, text, style=None, keep=False):
    """Add justified report prose with compact paragraph spacing."""
    paragraph = doc.add_paragraph(style=style)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.keep_together = keep
    run = paragraph.add_run(text)
    set_run_family(run)
    return paragraph


def add_heading(doc, level, text):
    """Add a numbered heading using Word's built-in heading style."""
    paragraph = doc.add_paragraph(style="Heading " + str(level))
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    set_run_family(run)
    return paragraph


def percent(value, digits=2):
    """Format a CSV fraction as a percent."""
    return f"{float(value) * 100:.{digits}f}"


def append_code(doc, path):
    """Append a Python file with Pygments-colored, indented source lines."""
    add_heading(doc, 2, path.name)
    source = path.read_text(encoding="utf-8-sig")
    lines = source.splitlines()
    for line in lines:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.left_indent = Inches(0.12)
        paragraph.paragraph_format.right_indent = Inches(0.04)
        ppr = paragraph._p.get_or_add_pPr()
        fill = OxmlElement("w:shd")
        fill.set(qn("w:fill"), "F5F5F0")
        ppr.append(fill)
        borders = OxmlElement("w:pBdr")
        edge = OxmlElement("w:left")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "12")
        edge.set(qn("w:space"), "5")
        edge.set(qn("w:color"), GREEN)
        borders.append(edge)
        ppr.append(borders)
        for token, value in lex(line + "\n", PythonLexer()):
            if value in ("\n", "\r\n"):
                continue
            run = paragraph.add_run(value)
            set_run(run, "Consolas", 8, color="1A1A1A")
            if token in Token.Comment:
                run.font.color.rgb = RGBColor.from_string("6B6B6B")
                run.italic = True
            elif token in Token.Keyword:
                run.font.color.rgb = RGBColor.from_string(GREEN)
                run.bold = True
            elif token in Token.Literal.String:
                run.font.color.rgb = RGBColor.from_string("9C4A1A")
            elif token in Token.Literal.Number:
                run.font.color.rgb = RGBColor.from_string("1F5FA8")
            elif token in Token.Name.Function or token in Token.Name.Class:
                run.font.color.rgb = RGBColor.from_string("7A3E9D")


def math_parts(source):
    """Translate the LaTeX fraction, script and symbol subset used in this report."""
    import re
    tokens = iter(re.findall(r'\\[A-Za-z]+|[{}_^]|.', source))
    symbols = {r'\rho':'ρ', r'\lambda':'λ', r'\mu':'μ', r'\le':'≤',
               r'\ne':'≠', r'\sum':'Σ', r'\int':'∫', r'\Delta':'Δ'}
    def node(tag, children=()):
        element = OxmlElement('m:' + tag)
        for child in children:
            element.append(child)
        return element
    def group():
        assert next(tokens) == '{'
        return parse()
    def parse():
        result = []
        for token in tokens:
            if token == '}':
                break
            if token == r'\frac':
                result.append(node('f', [node('num', group()), node('den', group())]))
            elif token in ('^', '_'):
                base = result.pop()
                tag, slot = ('sSup', 'sup') if token == '^' else ('sSub', 'sub')
                result.append(node(tag, [node('e', [base]), node(slot, group())]))
            else:
                text = node('t')
                text.text = symbols.get(token, token)
                text.set(qn('xml:space'), 'preserve')
                result.append(node('r', [text]))
        return result
    return parse()


def equation(doc, source, number):
    """Store a centered editable Word equation built from its LaTeX source."""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_together = True
    math = OxmlElement('m:oMath')
    math.extend(math_parts(source))
    paragraph._p.append(math)
    set_run(paragraph.add_run(f"     ({number})"), size=10)


def make_report():
    """Build the final report from current CSV results, figures and source files."""
    baseline = read_csv("baseline")
    sweep = read_csv("sweep")
    comparison = read_csv("comparison")
    validation = read_csv("validation")
    peak = [row for row in sweep if float(row["load"]) == 0.95]
    best = min(int(row["buffer"]) for row in peak
               if float(row["buffer_loss"]) <= 0.02
               and float(row["delay_s"]) <= 0.15)
    improved = next(row for row in peak if int(row["buffer"]) == best)
    constrained = next(row for row in peak if int(row["buffer"]) == 5)
    previous = max((row for row in peak if int(row["buffer"]) < best),
                   key=lambda row: int(row["buffer"]))
    errors = [row for row in validation if row["inside"] == "False"]

    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.54)
    section.left_margin = section.right_margin = Cm(2.54)

    # Apply Times New Roman to every document style before adding content.
    for style in doc.styles:
        if hasattr(style, "font"):
            set_font(style, size=11, name="Times New Roman")
    normal = doc.styles["Normal"]
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)
    set_font(doc.styles["Title"], size=20, name="Times New Roman",
             color=GREEN, bold=True)
    set_font(doc.styles["Heading 1"], size=15, name="Times New Roman",
             color=GREEN, bold=True)
    set_font(doc.styles["Heading 2"], size=12.5, name="Times New Roman",
             color=GREEN, bold=True)
    set_font(doc.styles["Caption"], size=10, name="Times New Roman")
    set_font(doc.styles["Footer"], size=10, name="Times New Roman")

    for name, before in (("Heading 1", 12), ("Heading 2", 8)):
        doc.styles[name].paragraph_format.space_before = Pt(before)
        doc.styles[name].paragraph_format.space_after = Pt(4)
    # The footer contains only a centered PAGE field.
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field_run = paragraph.add_run()
    set_run(field_run, size=10)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t")
    value.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instruction, separate, value, end):
        field_run._r.append(element)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("Limited Buffer Capacity in a Campus Wireless Gateway")
    set_run_family(title_run)
    title_properties = title._p.get_or_add_pPr()
    title_borders = OxmlElement("w:pBdr")
    bottom_rule = OxmlElement("w:bottom")
    bottom_rule.set(qn("w:val"), "single")
    bottom_rule.set(qn("w:sz"), "8")
    bottom_rule.set(qn("w:space"), "8")
    bottom_rule.set(qn("w:color"), GREEN)
    title_borders.append(bottom_rule)
    title_properties.append(title_borders)
    for text in ("Modeling and Simulation - Group A-2 - Group 2: Limited Buffer Capacity",
                 "Khulna University of Engineering & Technology (KUET)",
                 "Members and roll numbers: [Insert member names and roll numbers]",
                 "Course teacher: [Insert teacher name]",
                 "Date: [Insert submission date]"):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(text)
        set_run(run, size=10.5, color="000000")

    add_heading(doc, 1, "Abstract")
    add_paragraph(doc, f"This study models a university wireless gateway with four "
        f"Poisson traffic sources, a single FIFO server and a finite waiting buffer. "
        f"SimPy experiments compare a 1000-place baseline, a five-place constrained "
        f"gateway and an improved peak-load choice of {best} places. At offered load "
        f"0.95, the selected buffer rejected {percent(improved['buffer_loss'])}% "
        f"of arrivals and produced {1000 * float(improved['delay_s']):.2f} ms "
        f"mean delay, meeting the 2% loss and 150 ms delay targets. Twenty trials "
        f"of 250 s were run per setting after a 50 s warm-up. Finite-buffer queue "
        f"theory provides a reference for simulated loss and delay.")
    add_heading(doc, 1, "1. Introduction")
    add_paragraph(doc, "A shared wireless gateway must absorb packets that arrive "
        "while its transmission unit is busy. When waiting places are scarce, packets "
        "are rejected. Increasing the buffer reduces blocking but consumes memory "
        "and can increase delay. This project quantifies that trade-off for student, "
        "faculty, administrative and IoT traffic. It compares a large-buffer baseline, "
        "a constrained buffer and a right-sized design chosen from simulation results.")
    add_paragraph(doc, "The objective is to find the smallest tested buffer that "
        "meets the peak-load mean loss and delay limits while measuring memory, "
        "throughput and queue behavior under four offered loads.")

    add_heading(doc, 1, "2. System Definition (Task 1)")
    add_paragraph(doc, "Packets from four independent sources enter one gateway. "
        "The gateway contains a FIFO queue and one processing and transmission unit. "
        "After service, a wireless-channel error may corrupt a packet. Successful "
        "packets reach the destination; full-buffer arrivals are rejected.")
    add_figure(doc, "system_diagram.png", 1,
               "Modeled gateway, wireless channel, destination and loss paths.")
    add_caption(doc, "Table 1.", "System elements and boundary", True)
    add_table(doc, ["Element", "Model representation"],
        [["Entities", "Packets generated by four traffic sources"],
         ["Resources", "One gateway server; one wireless channel outcome per service"],
         ["Queue", "FIFO; B waiting places, excluding the packet in service"],
         ["Events", "Arrival, admission or rejection, service start, departure, corruption"],
         ["Inputs", "Class rates, μ, B, channel error probability, duration, seeds"],
         ["Outputs", "Loss, delivery, throughput, waits, delays, queue length, utilization"],
         ["Boundary", "Gateway arrival/admission through channel outcome; sources and destination outside"]])

    doc.add_page_break()
    add_heading(doc, 1, "3. Model Formulation (Task 2)")
    assumptions = [
        "Each source is an independent Poisson process. Exponential inter-arrivals "
        "make the total input Poisson and support an M/M/1/N reference.",
        "The gateway has one FIFO server with exponential service rate μ = 100 packets/s.",
        "B counts waiting places only. System capacity is N = B + 1, including service.",
        "A full system rejects a new packet immediately. No retry is modeled.",
        "Each completed service has independent channel corruption probability 0.05. "
        "There is no retransmission.",
        "Normal class rates are student 40, faculty 10, admin 10 and IoT 15 packets/s. "
        "All rates scale together to set ρ.",
        "Memory is payload capacity only, using 1500 bytes per waiting packet and "
        "1000 bytes per kilobyte."
    ]
    for index, item in enumerate(assumptions, 1):
        add_paragraph(doc, f"{index}. {item}")
    add_caption(doc, "Table 2.", "Model parameters and units", True)
    add_table(doc, ["Symbol", "Value", "Unit", "Distribution or meaning"],
        [["λstudent", "40 normal", "packets/s", "Poisson arrivals"],
         ["λfaculty", "10 normal", "packets/s", "Poisson arrivals"],
         ["λadmin", "10 normal", "packets/s", "Poisson arrivals"],
         ["λIoT", "15 normal", "packets/s", "Poisson arrivals"],
         ["ρ", "0.50, 0.75, 0.95, 1.10", "dimensionless", "λ / μ"],
         ["μ", "100", "packets/s", "Exponential service"],
         ["B", "1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 40, 50", "places", "Waiting capacity"],
         ["Bbaseline / Bconstrained", "1000 / 5", "places", "Reference designs"],
         ["p error", "0.05", "probability", "Bernoulli channel corruption"],
         ["Packet size", "1500", "bytes", "Fixed payload per packet"],
         ["Simulation / warm-up", "250 / 50", "s", "Per trial / excluded interval"],
         ["Trials / seeds", "20 / 1..20", "count", "Independent replications"],
         ["Loss / delay targets", "0.02 / 0.15", "fraction / s", "Peak-load design rule"]])

    add_paragraph(doc, "For a finite M/M/1/N queue, define λ as the total arrival "
        "rate, μ as the service rate, ρ = λ/μ, B as waiting capacity and N = B + 1. "
        "The stationary probability of a full system is the blocking probability.")
    equations = [
        r'\rho=\frac{\lambda}{\mu},   N=B+1',
        r'P_{B}=\frac{(1−\rho)\rho^{N}}{1−\rho^{N+1}}   (\rho\ne1)',
        r'L=\frac{\rho}{1−\rho}−\frac{(N+1)\rho^{N+1}}{1−\rho^{N+1}}   (\rho\ne1)',
        r'P_{B}=\frac{1}{N+1},   L=\frac{N}{2}   (\rho=1)',
        r'\lambda_{a}=\lambda(1−P_{B}),   L_{q}=L−\frac{\lambda_{a}}{\mu}',
        r'W_{q}=\frac{L_{q}}{\lambda_{a}},   W=W_{q}+\frac{1}{\mu}',
    ]
    for number, source in enumerate(equations, 1):
        equation(doc, source, number)
    add_paragraph(doc, "For measured arrivals, G denotes generated packets, R rejections, "
        "A admissions and D eventual deliveries. Dₜ counts successful departures from "
        "this cohort within the window of duration T. For admitted packet i, aᵢ, sᵢ and "
        "dᵢ denote arrival, service start and departure. Q(t) counts waiting packets.")
    metrics = [
        r'P_{loss}=\frac{R}{G},   P_{delivery}=\frac{D}{G},   X=\frac{D_{T}}{T}',
        r'W_{q,sim}=\frac{\sum_{i}(s_{i}−a_{i})}{A},   W_{sim}=\frac{\sum_{i}(d_{i}−a_{i})}{A}',
        r'L_{q,sim}=\frac{\int Q(t)dt}{T},   Q_{max}=max Q(t)',
        r'U=\frac{T_{busy}}{T},   M=\frac{1500B}{1000}   (KB)',
    ]
    for number, source in enumerate(metrics, 7):
        equation(doc, source, number)
    add_paragraph(doc, "The integral, maximum and busy time cover the measurement window. "
        "The reported maximum averages the trial maxima.")

    add_heading(doc, 1, "4. Simulation Method (Tasks 3 and 4)")
    steps = [
        "Four source processes draw exponential inter-arrivals using NumPy default_rng.",
        "Each packet checks the single SimPy Resource and joins the FIFO queue if capacity permits.",
        "Rejected packets are counted; admitted packets wait for service, then draw an exponential service time.",
        "After service, a Bernoulli draw determines delivery or channel corruption.",
        "Warm-up arrivals are excluded from packet metrics; queue and busy-time integrals cover the measurement window."
    ]
    for index, item in enumerate(steps, 1):
        add_paragraph(doc, f"{index}. {item}")
    add_paragraph(doc, "Each setting starts empty. Trials use seeds 1 through 20, each "
        "with 250 s total time and a 50 s warm-up, leaving 200 measured seconds. "
        "The 250 s duration was selected after quick mode took 75.50 s; 250 s × 20 "
        "trials took 685.34 s on the tested machine, below the 15-minute budget. "
        "The reported confidence half-width is 1.96 times the sample standard "
        "deviation across trials divided by the square root of 20. Theory predicts "
        "steady-state M/M/1/N loss and delay, while simulated intervals reflect "
        "finite independent runs.")
    add_paragraph(doc, "Validation tests all 12 finite buffer sizes at ρ = 0.75 and "
        "0.95 for both loss and delay. Figure 2 compares simulated blocking and "
        "theory; Table 3 lists every theory value outside the corresponding "
        "pointwise 95% interval.")
    add_figure(doc, "validation.png", 2,
               "Simulated and theoretical blocking probability across buffer sizes.")
    add_caption(doc, "Table 3.", "Validation warnings from the full run", True)
    warn_rows = []
    for row in errors:
        val = float(row["estimate"])
        ci = float(row["ci"])
        theory = float(row["theory"])
        reason = "Zero rejections observed in all trials" if ci == 0 else (
            "Theory below interval" if theory < val - ci else "Theory above interval")
        warn_rows.append([row["load"], row["buffer"], row["metric"],
                          f"{val:.5g} ± {ci:.3g}", f"{theory:.5g}", reason])
    add_table(doc, ["ρ", "B", "Metric", "Simulated mean ± half-width", "Theory", "Note"],
              warn_rows)
    add_paragraph(doc, "The full run placed theory inside 44 of 48 intervals. The "
        "four misses are individual outcomes among 48 comparisons, not evidence "
        "that each simulation is biased. The zero-loss case has a zero estimated "
        "half-width even though its theoretical loss is nonzero.")

    doc.add_page_break()
    add_heading(doc, 1, "5. Results")
    add_heading(doc, 2, "5.1 Baseline")
    add_paragraph(doc, "The 1000-place baseline recorded no buffer rejections in "
        "either comparison load across the measured trials. At ρ = 0.95 its mean "
        f"delay was {1000 * float(next(r for r in comparison if r['scenario']=='Baseline' and float(r['load'])==0.95)['delay_s']):.2f} ms, "
        "because a large queue absorbs bursts while packets wait for service.")
    add_heading(doc, 2, "5.2 Constrained network")
    add_paragraph(doc, "The five-place buffer used little memory but rejected more "
        "packets as load rose. Figures 3 and 4 show loss and waiting trends across "
        "the sweep; Figure 5 relates peak-load loss to memory. At peak load, the "
        f"constrained design used {float(constrained['memory_kb']):.1f} KB and "
        f"rejected {percent(constrained['buffer_loss'])}% of arrivals. Its mean wait "
        f"was {1000 * float(constrained['wait_s']):.2f} ms. At ρ = 1.10, the "
        "50-place buffer reduced loss relative to five places but increased delay, "
        "as a longer queue holds excess arrivals.")
    add_figure(doc, "loss_vs_buffer.png", 3,
               "Buffer loss across load levels; downward triangles mark zero observations.")
    add_figure(doc, "wait_vs_buffer.png", 4,
               "Mean waiting time across load levels.")
    add_figure(doc, "memory_tradeoff.png", 5,
               "Peak-load buffer loss against memory; vertical line marks the selected capacity.")
    add_heading(doc, 2, "5.3 Improved network")
    add_paragraph(doc, f"B_STAR is the smallest tested B with mean loss ≤ 0.02 "
        f"and mean delay ≤ 0.15 s at ρ = 0.95. The rule selected {best} places, "
        f"using {float(improved['memory_kb']):.1f} KB. Its loss was "
        f"{percent(improved['buffer_loss'])}% and mean delay was "
        f"{1000 * float(improved['delay_s']):.2f} ms. At the preceding tested "
        f"capacity B = {previous['buffer']}, loss was "
        f"{percent(previous['buffer_loss'])}% and delay was "
        f"{1000 * float(previous['delay_s']):.2f} ms, so that size failed the loss target.")
    add_heading(doc, 2, "5.4 Three-network comparison")
    add_paragraph(doc, "Table 4 compares all designs at normal and peak loads. Figure 6 "
        "shows their peak-load loss, delay and useful throughput.")
    add_caption(doc, "Table 4.", "Full-run comparison by offered load", True)
    rows = []
    for row in comparison:
        rows.append([row["load"], row["scenario"], row["buffer"],
                     f"{float(row['memory_kb']):.1f}",
                     percent(row["buffer_loss"]), percent(row["delivery_ratio"]),
                     f"{1000*float(row['wait_s']):.2f}",
                     f"{1000*float(row['delay_s']):.2f}",
                     f"{float(row['throughput_pps']):.2f}",
                     percent(row["utilization"])])
    add_table(doc, ["ρ", "Network", "B", "Memory (KB)", "Loss (%)", "Delivery (%)",
                    "Wait (ms)", "Delay (ms)", "Throughput (packets/s)", "Use (%)"], rows)
    add_figure(doc, "scenario_comparison.png", 6,
               "Peak-load comparison across the three gateway designs.")

    doc.add_page_break()
    add_heading(doc, 1, "6. Discussion (Task 7)")
    add_paragraph(doc, "Across the buffer sweep, larger B reduced rejection and "
        "increased memory. Waiting time also rose because packets could remain "
        "queued instead of being rejected. Under overload, finite memory reduced "
        "but could not eliminate loss because the average arrival rate exceeded "
        "the service rate. The right-sized design balances these effects for the "
        "chosen mean targets.")
    add_paragraph(doc, f"At peak load, increasing capacity from five to {best} "
        f"places added {float(improved['memory_kb'])-float(constrained['memory_kb']):.1f} KB, "
        f"reduced loss by {100*(float(constrained['buffer_loss'])-float(improved['buffer_loss'])):.2f} "
        f"percentage points and increased throughput by "
        f"{float(improved['throughput_pps'])-float(constrained['throughput_pps']):.2f} packets/s. "
        f"Mean wait rose by {1000*(float(improved['wait_s'])-float(constrained['wait_s'])):.2f} ms. "
        "Channel corruption remains after admission and is not improved by extra buffer.")
    add_paragraph(doc, "The M/M/1/N model is a simplified single-server network with "
        "no real campus traffic data. Poisson arrivals omit synchronized bursts; "
        "identical exponential service omits class-specific packet handling. The "
        "fixed warm-up and finite runs limit precision for rare losses. B_STAR "
        "depends directly on the 2% loss target, 0.15 s delay target and tested "
        "buffer list. It is a mean-based design choice, not a per-packet guarantee.")
    add_paragraph(doc, "For further work, collect campus arrival and service traces, "
        "test burst-aware inputs, and repeat the design search with longer runs and "
        "additional buffer sizes around the target boundary. Monitor loss and delay "
        "together before applying the selected capacity to a real gateway.")

    add_heading(doc, 1, "7. Conclusion")
    conclusions = [
        "Finite buffer capacity creates a measurable trade-off among memory, rejection and waiting time.",
        "At peak offered load ρ = 0.95, the five-place constrained gateway rejected 12.39% of arrivals.",
        f"The smallest tested buffer meeting both mean targets was B_STAR = {best}.",
        f"It used {float(improved['memory_kb']):.1f} KB, with {percent(improved['buffer_loss'])}% loss and {1000*float(improved['delay_s']):.2f} ms mean delay.",
        "The full run used 20 trials of 250 s with a 50 s warm-up and completed within 15 minutes.",
        "Theory was inside 44 of 48 pointwise validation intervals; four individual warnings remain documented.",
        "Real traffic measurements and longer trials are needed before deployment."
    ]
    for line in conclusions:
        add_paragraph(doc, line)

    add_heading(doc, 1, "References")
    for line in [
        "SimPy documentation. https://simpy.readthedocs.io",
        "Kleinrock, L. Queueing Systems, Vol. 1.",
        "Law, A. M. Simulation Modeling and Analysis."
    ]:
        add_paragraph(doc, line)

    doc.add_page_break()
    add_heading(doc, 1, "Appendix A. How to Run and Source Code")
    for line in [
        "1. Open the project directory in PyCharm.",
        "2. Select Python 3.10 or later as the interpreter.",
        "3. Install requirements with python -m pip install -r requirements.txt.",
        "4. Run main.py; set QUICK_MODE in config.py for a shorter check."
    ]:
        add_paragraph(doc, line)
    for filename in SOURCES:
        append_code(doc, ROOT / filename)

    math_settings = doc.settings.element.find(qn("m:mathPr"))
    if math_settings is not None:
        math_font = math_settings.find(qn("m:mathFont"))
        if math_font is not None:
            math_font.set(qn("m:val"), "Times New Roman")
    doc.save(OUT)
    print("Created", OUT)
    print("B_STAR", best, "validation warnings", len(errors))


if __name__ == "__main__":
    make_report()

