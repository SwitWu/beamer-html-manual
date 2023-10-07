from bs4 import BeautifulSoup, NavigableString
import re
import datetime
## process home.html

## write to file
def write_to_file(soup, filename):
    with open(filename, "w") as file:
        html = soup.encode(formatter="html5").decode("utf-8")
        lines = html.splitlines()
        new_lines = []
        for line in lines:
            # count number of spaces at the start of line
            spaces_at_start = len(re.match(r"^\s*", line).group(0))
            line = line.strip()
            # replace multiple spaces by a single space
            line = re.sub(' +', ' ', line)
            # restore indentation
            line = " " * spaces_at_start + line
            new_lines.append(line)
        html = "\n".join(new_lines)
        file.write(html)

def add_header(soup):
    header = soup.new_tag('header')

    hamburger = soup.new_tag('div')
    hamburger['id'] = "hamburger-button"
    hamburger.string = "☰"
    header.append(hamburger)

    h1 = soup.new_tag('strong')
    link = soup.new_tag('a', href="home.html")
    h1.append(link)
    link.append("Beamer Manual")
    header.append(h1)
    soup.find(class_="bodyandsidetoc").insert(0, header)

    # Docsearch 2
    # search_input = soup.new_tag('input', type="search", placeholder="Search..")
    # search_input['class'] = "search-input"
    # header.append(search_input)

    # link = soup.new_tag('link', rel="stylesheet", href="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.css")
    # soup.head.append(link)

    # script = soup.new_tag('script', src="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.js")
    # soup.body.append(script)
    # script = soup.new_tag('script')
    # script.append("""
    #   docsearch({
    #     apiKey: 'ae66ec3fc9df4b52b4d6f24fc8508fd3',
    #     indexName: 'tikz.dev',
    #     appId: 'Q70NNMA9GC',
    #     inputSelector: '.search-input',
    #     // Set debug to true to inspect the dropdown
    #     debug: false,
    # });
    # """)
    # soup.body.append(script)

    # Docsearch 3
    search_input = soup.new_tag('div', id="search")
    header.append(search_input)

    link = soup.new_tag('link', rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@docsearch/css@3")
    soup.head.append(link)

    script = soup.new_tag('script', src="https://cdn.jsdelivr.net/npm/@docsearch/js@3")
    soup.body.append(script)
    script = soup.new_tag('script')
    script.append("""
      docsearch({
        apiKey: '196e8c10ec187c9ae525dd5226fb9378',
        indexName: 'tikz',
        appId: 'JS6V5VZSDB',
        container: '#search',
        searchParameters: {
          filters: "tags:tikz",
        },
    });
    """)
    soup.body.append(script)

def add_footer(soup):
    footer = soup.new_tag('footer')
    footer_left = soup.new_tag('div')
    footer_left['class'] = "footer-left"
    # Link to license
    link = soup.new_tag('a', href="/license")
    link.string = "License"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to CTAN
    link = soup.new_tag('a', href="https://ctan.org/pkg/beamer")
    link.string = "CTAN"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to PDF version
    link = soup.new_tag('a', href="http://mirrors.ctan.org/macros/latex/contrib/beamer/doc/beameruserguide.pdf")
    link.string = "Official PDF version"
    footer_left.append(link)
    footer_left.append(" · ")
    # Issue tracker
    link = soup.new_tag('a', href="https://github.com/SwitWu/beamer-html-manual/issues")
    link.string = "Feedback and issues"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to About the HTML version
    link = soup.new_tag('a', href="https://github.com/SwitWu/beamer-html-manual")
    link.string = "Repository"
    footer_left.append(link)
    #
    footer.append(footer_left)
    footer_right = soup.new_tag('div')
    footer_right['class'] = "footer-right"
    today = datetime.date.today().isoformat()
    em = soup.new_tag('em')
    em.append("HTML version last updated: " + today)
    footer_right.append(em)
    footer.append(footer_right)
    soup.find('div', class_="bodyandsidetoc").append(footer)



with open("home.html", "r") as fp:
    soup = BeautifulSoup(fp, "html.parser")
    div = soup.find(class_ = "bodywithoutsidetoc")
    div["class"] = ["bodyandsidetoc", "grid-container"]
    add_footer(soup)
    add_header(soup)
    div = soup.new_tag("div")
    div["class"] = "sidetoccontainer"
    div["id"] = "chapter-toc-container"
    nav = soup.find("nav").extract()
    div.append(nav)
    soup.find(class_="bodyandsidetoc").insert(1, div)
    for a in soup.find_all('a', class_="tocsubsection"):
        a.parent.decompose()
    for a in soup.find_all('a', class_="tocsubsubsection"):
        a.parent.decompose()
    soup.find('div', class_="hidden").decompose()
    manual_title_block = soup.new_tag('div', attrs={"class": "manual-title-block"})
    manual_title = soup.new_tag('div', attrs={"class": "manual-title"})
    beamer = soup.new_tag('span', attrs={"class": "textsc"})
    beamer.string = "beamer"
    manual_title.extend(["The ", beamer, " Document Class"])
    manual_version = soup.new_tag('div', attrs={"class": "manual-version"})
    manual_version.string = "Manual for Version 3.7.0"
    manual_html_title = soup.new_tag('div', attrs={"class": "manual-html-title"})
    manual_html_title.string = "Unofficial HTML Version"
    manual_html_explanation = soup.new_tag('div', attrs={"class": "manual-html-explanation"})
    manual_html_explanation.string = "This HTML version of the documentation is maintained by Siyu Wu, and is produced with the help of the "
    lwarp = soup.new_tag('a', href="https://ctan.org/pkg/lwarp")
    lwarp.string = "lwarp"
    manual_html_explanation.append(lwarp)
    manual_html_explanation.append(" package")
    manual_authorship_explanation = soup.new_tag('div', attrs={"class": "manual-authorship-explanation"})
    manual_authorship_explanation.string = "Editors of the Beamer documentation: "
    Till = soup.new_tag('a', href="mailto:tantau@users.sourceforge.net")
    Till.string = "Till Tantau"
    Joseph = soup.new_tag('a', href="mailto:joseph.wright@morningstar2.co.uk")
    Joseph.string = "Joseph Wright"
    Vedran = soup.new_tag('a', href="mailto:vmiletic@inf.uniri.hr")
    Vedran.string = "Vedran Miletić"
    manual_authorship_explanation.extend([Till, ", ", Joseph, ", ", Vedran])
    manual_title_block.append(manual_title)
    manual_title_block.append(manual_version)
    manual_title_block.append(manual_html_title)
    manual_title_block.append(manual_html_explanation)
    manual_title_block.append(manual_authorship_explanation)
    section = soup.find('section')
    for child in section.children:
        if child.name == 'p':
            child.decompose()
    section.h4.decompose()
    soup.find('pre', class_="verbatim").insert_before(manual_title_block)
    write_to_file(soup, "processed/home.html")

print("Finished")
