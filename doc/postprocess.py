from unicodedata import name
from xml.dom import minidom
from bs4 import BeautifulSoup, Comment, NavigableString
from shutil import copyfile, copytree
import json
import re
import os
import datetime
import subprocess

double_newline_pattern = re.compile(r'\n( )*\n$')

def kilobytes(filename):
    st = os.stat(filename)
    return st.st_size / 1000

# mkdir processed
os.makedirs("processed", exist_ok=True)
copyfile("style.css", "processed/style.css")
copyfile("home.html", "processed/home.html")
copyfile("beameruserguide.js", "processed/beameruserguide.js")
copyfile("lwarp-mathjax-emulation.js", "processed/lwarp-mathjax-emulation.js")
copytree("beameruserguide-images", "processed/beameruserguide-images", dirs_exist_ok=True)
copytree("beamerthemeexample", "processed/beamerthemeexample", dirs_exist_ok=True)
copytree("navigation-symbols", "processed/navigation-symbols", dirs_exist_ok=True)
# copytree("banners/social-media-banners", "processed/social-media-banners", dirs_exist_ok=True)
# copytree("banners/toc-banners", "processed/toc-banners", dirs_exist_ok=True)

def add_js(soup):
    script = soup.new_tag("script", src="beameruserguide.js")
    soup.head.append(script)

def specific_div_class_names(name):
    if(name in ['command', 'environment', 'element', "class", "package", "theme", "beameroption", "solution"]):
        return True
    else:
        return False

def remove_unnecessary_lists(soup):
    for div in soup.find_all('div', class_ = specific_div_class_names):
        while div.ul != None:
            div.ul.unwrap()
        while div.li != None:
            div.li.unwrap()

def remove_empty_p(soup):
    for p in soup.find_all('p'):
        if p.contents == [] or p.contents == ["\n"]:
            p.decompose()

## table of contents and anchor links
def rearrange_heading_anchors(soup):
    heading_tags = ["h4", "h5", "h6"]
    for tag in soup.find_all(heading_tags):
        entry = tag.find()
        assert "class" in entry.attrs and "sectionnumber" in entry["class"]
        entry.string = entry.string.replace("\u2003", "").strip()
        anchor = "sec-" + entry.string
        entry["id"] = anchor 
        for index, content in enumerate(tag.contents): 
            if isinstance(content, str):
                space = NavigableString(' ')
                tag.insert(index, space) 
                break                   

        # add paragraph links
        if tag.name in ["h5", "h6"]:
            # wrap the headline tag's contents in a span (for flexbox purposes)
            headline = soup.new_tag("span")
            for child in reversed(tag.contents):
                headline.insert(0, child.extract())
            tag.append(headline)
            link = soup.new_tag('a', href=f"#{anchor}")
            link['class'] = 'anchor-link'
            link.append("¶")
            tag.append(link)
        # find human-readable link target and re-arrange anchor
        for sibling in tag.next_siblings:
            if sibling.name is None:
                continue
            if sibling.name == 'a' and 'id' in sibling.attrs:
                # potential link target
                if 'beameruserguide-auto' in sibling['id']:
                    continue
                # print(f"Human ID: {tag['id']} -> {sibling['id']}")
                # found a human-readable link target
                a_tag = sibling.extract()
                tag.insert(0, a_tag)
                break
            else:
                break

# right-hand side toc for every section
def make_local_toc(soup):
    container = soup.find(class_="bodyandsidetoc")
    toc_container = soup.new_tag('div')
    toc_container['class'] = 'sidetoccontainer'
    toc_container['id'] = 'local-toc-container'
    toc_nav = soup.new_tag('nav')
    toc_nav['class'] = 'sidetoc'
    toc_container.append(toc_nav)
    toctitle = soup.new_tag('div')
    toctitle['class'] = 'sidetoctitle'
    toctitle_text = soup.new_tag('p')
    toctitle_text.append("On this page")
    toctitle.append(toctitle_text)
    toc_nav.append(toctitle)
    toc = soup.new_tag('div')
    toc['class'] = 'sidetoccontents'
    toc_nav.append(toc)
    heading_tags = ["h5", "h6"]
    for tag in soup.find_all(heading_tags):
        anchor = tag.find(class_="sectionnumber").get('id')
        item = soup.new_tag('p')
        a = soup.new_tag('a', href=f"#{anchor}")
        toc_string = tag.text.strip().replace("¶", "")
        sectionnumber = tag.find(class_="sectionnumber").text.strip()
        toc_string = toc_string.replace(sectionnumber, "")
        a.string = toc_string.strip()
        if tag.name == "h5":
            a['class'] = 'tocsubsection'
        elif tag.name == "h6":
            a['class'] = 'tocsubsubsection'
        item.append(a)
        toc.append(item)
    container.insert(0,toc_container)

def add_class(tag, c):
    if 'class' in tag.attrs:
        tag['class'].append(c)
    else:
        tag['class'] = [c]

# def _add_mobile_toc(soup):
#     "on part overview pages, add a list of sections for mobile users"
#     mobile_toc = soup.new_tag('div')
#     mobile_toc['class'] = 'mobile-toc'
#     mobile_toc_title = soup.new_tag('strong')
#     mobile_toc_title.string = "Sections"
#     mobile_toc.append(mobile_toc_title)
#     mobile_toc_list = soup.new_tag('ul')
#     mobile_toc.append(mobile_toc_list)
#     # get toc contents
#     toc_container = soup.find(class_="sidetoccontainer")
#     toc_items = toc_container.find_all('a', class_="tocsection")
#     for item in toc_items:
#         li = soup.new_tag('li')
#         a = soup.new_tag('a', href=item.get('href'))
#         a.string = item.text
#         li.append(a)
#         mobile_toc_list.append(li)
#     # add toc to section class="textbody", after the h2
#     textbody = soup.find(class_="textbody")
#     h2_index = textbody.contents.index(soup.h2)
#     textbody.insert(h2_index+1, mobile_toc)

# def make_breadcrumb(soup, breadcrumb):
#     # example for breadcrumb parameter:
#     # breadcrumb = [
#     #                {"name": "Parent", "item": "https://.."},
#     #                {"name": "This page", "item": "https://.."}
#     #            ]
#     # make JSON-LD for Google
#     breadcrumb_json = {
#         "@context": "https://schema.org",
#         "@type": "BreadcrumbList",
#         "itemListElement": []
#     }
#     for i, item in enumerate(breadcrumb):
#         breadcrumb_json["itemListElement"].append({
#             "@type": "ListItem",
#             "position": i+1,
#             "name": item["name"],
#             "item": item["item"]
#         })
#     script = soup.new_tag('script', type="application/ld+json")
#     script.string = json.dumps(breadcrumb_json, indent=4)
#     soup.head.append(script)

# used to modify the links in home page, this function is actually an excerpt of the next function
def normalize_link(soup):
    nav = soup.find("nav", class_="toc")
    for p in nav.children:
        if p.name != 'p':
            continue
        filename = p.a["href"].split("#")[0]
        p.a["href"] = filename

## shorten sidetoc
def shorten_sidetoc_and_add_part_header(soup, is_home=False):
    container = soup.find(class_="sidetoccontainer")
    container['id'] = "chapter-toc-container"
    sidetoc = soup.find(class_="sidetoccontents")
    if soup.h4 is None:
        my_file_id = soup.h2['id']    
        is_a_section = False
    else:
        my_file_id = soup.h4['id']
        is_a_section = True
    toc = []
    last_part = None
    my_part = None
    for entry in sidetoc.children:
        if entry.name != 'p':
            continue
        # Skip home link
        # if entry.a['href'] == "index.html":
        #     continue
        if "linkhome" in entry.a['class']:
            entry.decompose()
            continue
        if len(entry.a['href'].split('#')) < 2:
            print(f"WARNING: {entry.a['href']}")
        filename = entry.a['href'].split('#')[0]
        file_id = entry.a['href'].split('#')[1]
        entry.a['href'] = filename # get rid of autosec in toc, not needed
        # get rid of sectionnumber
        new_a = soup.new_tag('a', href=entry.a['href'])
        new_a['class'] = entry.a['class']
        contents = entry.a.contents[2:]
        contents[0] = contents[0][1:]
        new_a.extend(contents)
        entry.a.replace_with(new_a)
        # Skip introduction link because it doesn't have a part
        if entry.a['href'] == "index-0":
            entry.a['class'] = ['linkintro']
            if is_home:
                entry['class'] = ['current']
            continue
        if "tocpart" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
                "children": []
            }
            last_part = element
            toc.append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                soup.title.string = entry.a.get_text() + " - Beamer Manual"
                my_part = element
        elif "tocsection" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
            }
            if last_part:
                last_part['children'].append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                my_part = last_part
                my_title = entry.a.get_text()
                my_href = entry.a.get('href')
                soup.title.string = my_title + " - Beamer Manual"
        else:
            print(f"unknown class: {entry.a['class']}")
    for part in toc:
        if part != my_part:
            for section in part['children']:
                section['tag'].decompose()
        else:
            add_class(part['tag'], "current-part")
            for section in part['children']:
                add_class(section['tag'], "current-part")
            if is_a_section:
                h2 = soup.new_tag('h2')
                h2['class'] = ['inserted']
                # contents = part['tag'].a.contents[1:]
                # h2.append(contents[1].replace("\u2003", ""))
                part_name = part['tag'].a.get_text()
                assert part_name is not None
                h2.append(part_name)
                soup.h1.insert_after(h2)
                # breadcrumb = [
                #     {"name": part_name, "item": "https://tikz.dev/" + part['tag'].a.get('href')},
                #     {"name": my_title, "item": "https://tikz.dev/" + my_href}
                # ]
                # make_breadcrumb(soup, breadcrumb)
    # if not is_a_section and not is_home:
    #     # this is a part overview page
    #     # let's insert an additional local table of contents for mobile users
    #     _add_mobile_toc(soup)

## make anchor tags to definitions
def get_entryheadline_p(tag):
    for child in tag.find_all(name="p"):
        if child.name is not None:
            if child.name == 'p':
                return child
    return None
def get_entryheadline_a(p_tag):
    for child in p_tag.children:
        if child.name is not None:
            if child.name == 'a':
                return child
    return None
def make_entryheadline_anchor_links(soup):
    for tag in soup.find_all(class_="entryheadline"):
        p_tag = get_entryheadline_p(tag)
        if p_tag is None:
            continue
        a_tag = get_entryheadline_a(p_tag)
        if a_tag is None:
            continue
        anchor = a_tag.get('id')
        if "pgf" not in anchor:
            continue
        # make anchor prettier
        pretty_anchor = anchor.replace("pgf.back/","\\").replace("pgf./","")
        link = soup.new_tag('a', href=f"#{pretty_anchor}")
        link['class'] = 'anchor-link'
        link['id'] = pretty_anchor
        link.append("¶")
        p_tag.append(link)


## remove a tag from the themeexample-image div
# def remove_a_tag_from_themeexample(soup):
#     for div in soup.find_all('div', class_ = 'themeexample-image'):
#         div.a.unwrap()

## delete style attribute of img tag
# def del_style_attribute_from_themeexample_img(soup):
#     for div in soup.find_all('div', class_ = 'themeexample-image'):
#         del div.img['style']

## remove the last possible empty line in the contents of pre tag
def remove_empty_line_from_pre(soup):
    for pre_tag in soup.find_all('pre', class_ = 'verbatim'):
        if (pre_tag.string == None):
            continue
        else:
            pre_tag.string.replace_with(re.sub(double_newline_pattern, r'\n', pre_tag.string))

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

def remove_mathjax_if_possible(filename, soup):
    with open(filename, "r") as file:
        content = file.read()
        if content.count("\(") == 60:
            # mathjax isn't actually used
            soup.find(class_="hidden").decompose()
            # remove element with id "MathJax-script"
            soup.find(id="MathJax-script").decompose()
            # go through all script tags and remove the ones that contain the word "emulation"
            for tag in soup.find_all('script'):
                if "Lwarp MathJax emulation code" in tag.string:
                    tag.decompose()
                    break
        else:
            soup.find(id="MathJax-script").attrs['async'] = None
            # externalize emulation code
            for tag in soup.find_all('script'):
                # print(tag.string)
                if tag.string is not None and "Lwarp MathJax emulation code" in tag.string:
                    tag.decompose()
                    script = soup.new_tag('script', src="lwarp-mathjax-emulation.js")
                    script.attrs['async'] = None
                    soup.head.append(script)
                    break

def remove_useless_elements(soup):
    soup.find("h1").decompose()
    soup.find(class_="topnavigation").decompose()
    soup.find(class_="botnavigation").decompose()

def addClipboardButtons(soup):
    for example in soup.find_all(class_="example-code"):
        button = soup.new_tag('button', type="button")
        button['class'] = "clipboardButton"
        button.string = "copy"
        example.insert(0,button)

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
        apiKey: '09762da49fe4ba391f7a3618c73720d8',
        indexName: 'beamerplusio',
        appId: 'WNNAN5R8GM',
        container: '#search',
        searchParameters: {
          filters: "tags:beamer",
        },
    });
    """)
    soup.body.append(script)

def favicon(soup):
    link = soup.new_tag('link', rel="icon", type="image/png", sizes="16x16", href="beameruserguide-images/favicon.png")
    soup.head.append(link)


## add footer contents
def add_footer(soup):
    footer = soup.new_tag('footer')
    footer_left = soup.new_tag('div')
    footer_left['class'] = "footer-left"
    # Link to license
    link = soup.new_tag('a', href="Licenses-Copyright.html")
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

# def _add_dimensions(tag, svgfilename):
#     with open(svgfilename, "r") as svgfile:
#         svg = minidom.parse(svgfile)
#         width_pt = svg.documentelement.getattribute("width").replace("pt", "")
#         height_pt = svg.documentelement.getattribute("height").replace("pt", "")
#     width_px = float(width_pt) * 1.33333
#     height_px = float(height_pt) * 1.33333
#     tag['width'] = "{:.3f}".format(width_px)
#     tag['height'] = "{:.3f}".format(height_px)
#     return (width_px, height_px)

# def process_images(soup):
#     for tag in soup.find_all("img"):
#         if "svg" in tag['src']: 
#             width_px, height_px = _add_dimensions(tag, tag['src'])
#             # very large SVGs are pathological and empty, delete them
#             if height_px > 10000:
#                 tag.decompose()
#                 continue
#             tag["loading"] = "lazy"
#             # replace all SVGs by PNGs except if that's a big filesize penalty
#             # doing this because the SVGs are missing some features like shadows
#             png_filename = tag['src'].replace("svg", "png")
#             if kilobytes(png_filename) < 5 * kilobytes(tag['src']):
#                 tag['src'] = png_filename
#     for tag in soup.find_all("object"):
#         if "svg" in tag['data']: 
#             _add_dimensions(tag, tag['data'])

def rewrite_svg_links(soup):
    for tag in soup.find_all("a"):
        if tag.has_attr('href') and "svg" in tag['href']:
            img = tag.img
            if img and "inlineimage" in img['class']:
                object = soup.new_tag('object')
                object['data'] = img['src']
                object['type'] = "image/svg+xml"
                tag.replace_with(object)

def add_version_to_css_js(soup):
    "to avoid caching, add a version number to the URL"
    today = datetime.date.today().isoformat().replace("-", "")
    for tag in soup.find_all("link"):
        if tag.has_attr('href') and tag['href'] == "style.css":
            tag['href'] += "?v=" + today
    for tag in soup.find_all("script"):
        if tag.has_attr('src') and tag['src'] == "pgfmanual.js":
            tag['src'] += "?v=" + today

# def semantic_tags(soup):
#     for example in soup.find_all(class_="example"):
#         example.name = "figure"
#     for examplecode in soup.find_all(class_="example-code"):
#         p = examplecode.find("p")
#         p.name = "code"

# def add_meta_tags(filename, soup):
#     stem = os.path.splitext(filename)[0]
#     # title
#     if filename == "index-0.html":
#         soup.title.string = "Beamer--Complete Online Documentation"
#     # descriptions
#     if filename == "index-0.html":
#         meta = soup.new_tag('meta', content="Full online version of the documentation of Beamer.")
#         meta['name'] = "description"
#         soup.head.append(meta)
#         og_meta = soup.new_tag('meta', property="og:description", content="Full online version of the documentation of Beamer.")
#         soup.head.append(og_meta)
#     elif stem in meta_descriptions:
#         meta = soup.new_tag('meta', content=meta_descriptions[stem])
#         meta['name'] = "description"
#         soup.head.append(meta)
#         og_meta = soup.new_tag('meta', property="og:description", content=meta_descriptions[stem])
#         soup.head.append(og_meta)
#     # canonical
#     if filename == "index-0.html":
#         link = soup.new_tag('link', rel="canonical", href="https://tikz.dev/")
#         soup.head.append(link)
#         meta = soup.new_tag('meta', property="og:url", content="https://tikz.dev/")
#         soup.head.append(meta)
#     else:
#         link = soup.new_tag('link', rel="canonical", href="https://tikz.dev/" + stem)
#         soup.head.append(link)
#         meta = soup.new_tag('meta', property="og:url", content="https://tikz.dev/" + stem)
#         soup.head.append(meta)
#     # thumbnail
#     img_filename = "social-media-banners/" + stem + ".png"
#     if filename == "index-0.html":
#         img_filename = "social-media-banners/introduction.png"
#     if os.path.isfile("banners/"+img_filename):
#         meta = soup.new_tag('meta', property="og:image", content="https://tikz.dev/" + img_filename)
#         soup.head.append(meta)
#         # allow Google Discover
#         meta = soup.new_tag('meta', content="max-image-preview:large")
#         meta['name'] = "robots"
#         soup.head.append(meta)
#     # og.type = article
#     meta = soup.new_tag('meta', property="og:type", content="article")
#     soup.head.append(meta)
#     # get og.title from soup.title
#     meta = soup.new_tag('meta', property="og:title", content=soup.title.string)
#     soup.head.append(meta)
#     # twitter format
#     meta = soup.new_tag('meta', content="summary_large_image")
#     meta['name'] = "twitter:card"
#     soup.head.append(meta)
#
# def add_spotlight_toc(filename):
#     spotlight_files = ["index", "tutorials-guidelines", "tikz", "libraries", "gd", "dv"]
#     if not any(filename == x + ".html" for x in spotlight_files):
#         return
#     # read as string
#     with open("processed/"+filename, "r") as f:
#         html = f.read()
#     # read replacement string
#     with open("spotlight-tocs/spotlight-toc-"+filename, "r") as f:
#         toc = f.read()
#     # replace
#     if filename == "index.html":
#         html = html.replace('<div class="titlepagepic">', toc)
#     else:
#         html = html.replace('</section>', toc+'</section>')
#     # write back
#     with open("processed/"+filename, "w") as f:
#         f.write(html)

# def add_pgfplots_ad(filename):
#     if not "index" in filename:
#         return
#     with open("processed/"+filename, "r") as f:
#         html = f.read()
#         html = html.replace('<div id="search"></div>', """<!-- temporary ad for new pgfplots pages -->
#         <div id="pgfplots-link">
#           <a href="https://tikz.dev/pgfplots">
#             <span id="pgfplots-desktop-version">
#               NEW:
#               <span class="pgfplots-link-text">tikz.dev/PGFplots</span>
#             </span>
#             <span id="pgfplots-smaller-version">
#               NEW:
#               <span class="pgfplots-link-text">PGFplots</span>
#             </span>
#           </a>
#         </div>
#         <div id="search"></div>""")
#     with open("processed/"+filename, "w") as f:
#         f.write(html)

# def handle_code_spaces(soup):
#     # these are throwaway tags, only used to avoid overfull boxes
#     for tag in soup.find_all(class_="numsp"):
#         tag.decompose()
#     # some links within codes have extra spaces, strip them
#     for codeblock in soup.find_all(class_="example-code"):
#         for link in codeblock.find_all("a"):
#             link.string = link.string.strip()

for filename in sorted(os.listdir()):
    if filename.endswith(".html"):
        if filename in ["home.html", "beameruserguide_html.html"]:
            continue
        else:
            print(f"Processing {filename}")
            with open(filename, "r") as fp:
                soup = BeautifulSoup(fp, 'html.parser')
                add_footer(soup)
                shorten_sidetoc_and_add_part_header(soup, is_home=(filename == "index-0.html"))
                rearrange_heading_anchors(soup)
                make_local_toc(soup)
                # remove_mathjax_if_possible(filename, soup)
                remove_useless_elements(soup)
                rewrite_svg_links(soup)
                add_version_to_css_js(soup)
                add_header(soup)
                add_js(soup)
                remove_unnecessary_lists(soup)
                favicon(soup)
                remove_empty_line_from_pre(soup)
                remove_empty_p(soup)
                soup.find(class_="bodyandsidetoc")['class'].append("grid-container")
                write_to_file(soup, "processed/"+filename)

# def numspace_to_spaces(filename):
#     "replace numspaces by normal spaces in code blocks"
#     with open("processed/"+filename, "r") as f:
#         html = f.read()
#     for num_copies in range(30,1,-1):
#         pattern = "&numsp;"*num_copies
#         replacement = '<span class="spaces">'+' '*num_copies+'</span>'
#         html = html.replace(pattern, replacement)
#     for opener in [">", "}", "]", ","]:
#         for closer in ["<", "{", "["]:
#             pattern = opener+"&numsp;"+closer
#             replacement = opener+" "+closer
#             html = html.replace(pattern, replacement)
#     html = html.replace("&numsp;", '<span class="spaces"> </span>')
#     # ugly hack to fix https://github.com/DominikPeters/tikz.dev-issues/issues/16
#     html = html.replace('<a href="drivers#pgf.class">class</a>', 'class')
#     with open("processed/"+filename, "w") as f:
#         f.write(html)

# for filename in sorted(os.listdir()):
#     if filename.endswith(".html"):
#         if filename in ["index-0.html", "description.html", "pgfmanual_html.html", "home.html"] or "spotlight" in filename:
#             continue
#         else:
#             numspace_to_spaces(filename)

print("Processing home.html")
with open("home.html", "r") as file:
    soup = BeautifulSoup(file, "html.parser")
    title = soup.find("title")
    title.string = "Beamer Manual - Complete HTML Documentation"
    div = soup.find("body")
    div["class"] = "home-page"
    div = soup.find(class_ = "bodywithoutsidetoc")
    div["class"] = ["bodyandsidetoc", "grid-container"]
    add_footer(soup)
    add_js(soup)
    add_header(soup)
    remove_empty_line_from_pre(soup)
    normalize_link(soup)
    favicon(soup)
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
    # soup.find('div', class_="hidden").decompose()
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


# prettify
# run command with subprocess
print("Prettifying")
subprocess.run(["npx", "prettier", "--write", "processed/*.html"])

print("Finished")
