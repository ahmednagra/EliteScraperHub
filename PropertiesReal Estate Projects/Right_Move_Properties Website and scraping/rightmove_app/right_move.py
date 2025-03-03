import re
import ssl
from io import BytesIO

import requests

ssl._create_default_https_context = ssl._create_unverified_context

import json
import os
from collections import OrderedDict
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from scrapy import Spider, Request, signals, Selector

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Image, Table, TableStyle, PageBreak, PageTemplate, Frame, Spacer
from reportlab.platypus import BaseDocTemplate
from slugify import slugify

styles = getSampleStyleSheet()
custom_style_title = ParagraphStyle('CustomStyleTitle', parent=styles['Heading1'], fontSize=14, spaceAfter=0)
custom_style_content = ParagraphStyle('CustomStyleContent', parent=styles['Normal'], fontSize=10, leading=12, spaceAfter=3, fontName='Helvetica')
doc = None

# Custom styles Header & Title in Center
custom_style_title_center = ParagraphStyle('CustomStyleTitleCenter', parent=styles['Heading1'], fontSize=14, spaceAfter=0, alignment=TA_CENTER)


# Function to get value by heading
def get_value_by_heading(selector, heading, letting_details=False):
    if letting_details:
        return selector.css(f'dt:contains("{heading}") + dd::text').get(default='').strip()
    else:
        return selector.css(f'dl:contains("{heading}") dd::text').get(default='').strip()


# Function to get images from the response
def get_images(selector):
    property_images = []
    try:
        json_data = json.loads(
            selector.css('script:contains("propertyData")::text').re_first(r'window.PAGE_MODEL = (.*)'))
        property_json = json_data.get('propertyData', {}) or {}
        property_images = [image.get('url') for image in property_json.get('images', [{}])]
        floor_plan_image = property_json.get('floorplans', [{}])[0].get('url') or None
    except json.JSONDecodeError:
        floor_plan_image = None
        property_images = []
    except AttributeError:
        floor_plan_image = None
        property_images = []
    except IndexError:
        floor_plan_image = None

    floor_plan = floor_plan_image or selector.css('a[href*="plan"] img::attr(src)').get('').replace('_max_296x197',
                                                                                                    '')
    image_urls = property_images or selector.css(
        'a[itemprop="photo"] [itemprop="contentUrl"]::attr(content)').getall()

    image_items = {f'Image {index}': '' for index in range(1, 11)}

    # return {f'Image {index + 1}': image_url for index, image_url in enumerate(image_urls)}
    image_items.update(
        {f'Image {index + 1}': f'=IMAGE("{image_url}")' for index, image_url in enumerate(image_urls)})
    image_items.update({'Floor Plan': f'=IMAGE("{floor_plan}")'})

    return image_items, image_urls, floor_plan


def create_images_table(item):
    """this method create a table of property images 4 rows and 2 cols """
    image_list = []

    # New width and height after adjustment
    new_width = 3.5 * inch  # inches (increased width)
    new_height = 2 * inch  # inches (decreased height)
    images_urls = item.get('image_urls', [])

    for image_url in images_urls[:8]:
        if image_url:
            image = Image(image_url, width=new_width, height=new_height)  # Adjust width and height
            image_list.append(image)

    num_images = len(image_list)
    if num_images % 2 != 0:
        image_list.append(Spacer(new_width, new_height))  # Add a spacer if the number of images is odd

    # Create the image table with two columns and four rows
    rows = [image_list[i:i + 2] for i in range(0, len(image_list), 2)]
    image_table = Table(rows, colWidths=[new_width, new_width])  # Adjust column widths

    image_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 3, colors.white),  # Add border to all cells
    ]))

    return image_table


def pdf_page_header(canvas, doc):
    try:
        logo_width = 0.75 * inch
        logo_height = 0.75 * inch  # Increase the height of the logo to 0.75 inch
        logo_x = doc.leftMargin
        logo_y = doc.height + doc.topMargin - logo_height

        # previous
        # canvas.drawImage("input/logo.PNG", logo_x, logo_y, width=logo_width, height=logo_height)

        # Correct path to the logo image
        logo_path = os.path.join('rightmove_app', 'assets', 'input', 'logo.PNG')

        canvas.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)
    except OSError:
        print("Error loading logo image")

    pickup_line_style = ParagraphStyle(
        'PickupLineStyle', parent=styles['Normal'], fontSize=10, textColor='black',
        spaceAfter=1, alignment=2, leading=7  # Adjust the leading value to reduce space between lines
    )

    listed_by = '''NIKO RELOCATION<br/>
                    nikoinlondon@outlook.com<br/>
                    Wechat: nikoinlondon <br/>
                    www.nikorelocation.co.uk
                  '''
    pickup_line_text = listed_by.replace('\n', '<br/>')
    pickup_line_paragraph = Paragraph(pickup_line_text, pickup_line_style)

    # Adjust vertical position to place the pickup line below the logo
    pickup_line_y = doc.height + doc.topMargin - logo_height - 0.2 * inch
    top_margin = 0.5 * inch
    pickup_line_paragraph.wrapOn(canvas, doc.width - logo_width - 10, doc.topMargin)
    pickup_line_paragraph.drawOn(canvas, doc.width - pickup_line_paragraph.width - 10, pickup_line_y)


def add_floor_plan_image(item):
    image_list = []

    # New width and height after adjustment
    new_width = 7 * inch  # Full width of the page
    new_height = 8.3 * inch  # Full height of the page

    floor_plane_image_url = item.get('Floor Plan image url')

    if floor_plane_image_url:
        image = Image(floor_plane_image_url, width=new_width, height=new_height)  # Adjust width and height
        # image_list.append(image)
        image_list.append([image])

    # Create the image table with a single row and a single column containing the image
    image_table = Table(image_list, colWidths=new_width, rowHeights=new_height)

    image_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 3, colors.white),  # Add border to the cell
    ]))

    return image_table


def get_bullet_points(item_list):
    """ This method add bullets in list items and convert into string"""
    bullet_points = "\n".join(f"• {item}" for item in item_list)

    return bullet_points


def make_pdf(item, response):
    """This method make the pdf file of given content.
     it gets some content from item and other value like letting and key features getting from response """

    bed_room = item.get('Bedrooms').replace('×', '')
    bath_room = item.get('Bathrooms').replace('×', '')
    price = item.get('Price PW', '')
    price_bed_bath_values = f'<font bgcolor="{HexColor("#A6F79B ")}">{price} </font> | {bed_room} Bedroom | {bath_room} Bathroom'
    address = item.get('Address', '')

    letting_details_headers = response.css('._2RnXSVJcWbWv4IpBC1Sng6 dt::text').getall()
    letting_details_value = response.css('._2RnXSVJcWbWv4IpBC1Sng6 dd::text').getall()

    letting_details = [f"{label}{value}" for label, value in zip(letting_details_headers, letting_details_value)]
    letting_details = get_bullet_points(letting_details).replace('\n', '<br/>')

    key_features = get_bullet_points(response.css('.lIhZ24u1NHMa5Y6gDH90A ::text').getall()).replace('\n', '<br/>')

    # Create a BytesIO object to hold the PDF content
    pdf_buffer = BytesIO()

    # Use BaseDocTemplate with the BytesIO buffer instead of file path
    doc = BaseDocTemplate(pdf_buffer, title='Properties', pagesize=letter, leftMargin=20, topMargin=15, rightMargin=6,
                          bottomMargin=6)

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 50)
    header_template = PageTemplate(frames=[frame], onPage=pdf_page_header)
    doc.addPageTemplates(header_template)

    content = [
        # previous
        # Paragraph(f'<br/><br/>{address.title()}', custom_style_title),
        # Paragraph(f'{price_bed_bath_values}<br/>', custom_style_title),

        Paragraph(f'<br/><br/>{address.title()}', custom_style_title_center),  # Center-align title
        Paragraph(f'{price_bed_bath_values}<br/>', custom_style_title_center),  # Center-align price and details
        Paragraph(f'<br/>', custom_style_content),
        create_images_table(item),
        Paragraph(f'<br/>', custom_style_content),
        PageBreak()
    ]

    floor_plane_image_url = item.get('Floor Plan image url', '')

    if floor_plane_image_url:
        content.append(Paragraph(f'<br/><br/>', custom_style_title))
        content.append(add_floor_plan_image(item))
        content.append(PageBreak())

    # previous
    # property_id = ''.join(response.url.split('/')[-1:])

    property_id = re.search(r'/properties/(\d+)', response.response.url)
    property_id = property_id.group(1) if property_id else ''
    property_id_custom_style_content = ParagraphStyle(
        'CustomStyleContent', parent=styles['Normal'], fontSize=10, textColor='black',
        spaceBefore=10, alignment=2, leading=10, rightIndent=40
    )

    content.append(Paragraph(f'<br/>{property_id}', property_id_custom_style_content))

    if letting_details:
        content.append(Paragraph(f'<br/><u>Letting Details</u>:', custom_style_title))
        content.append(Paragraph(f'{letting_details}', custom_style_content))

    if key_features:
        content.append(Paragraph(f'<br/><u>key Features:</u>', custom_style_title))
        content.append(Paragraph(f'{key_features}', custom_style_content))

    doc.build(content)

    # Reset the buffer's position to the beginning for reading
    pdf_buffer.seek(0)

    a = pdf_buffer.read()
    return a


# Main function to scrape data
def main(url):

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = []
    error = ''

    try:
        print('Requested URL:', url)
        response = requests.get(url, headers=headers)

        if response.status_code == 410:
            error = f'URL {url} returned 410 status code \n\n'
            print(error)
            return '', [], '', error

        if response.status_code != 200:
            error = f'Error {response.status_code} occurred while fetching URL: {url} \n\n'
            print(error)
            return '', [], '', error

        selector = Selector(response)
        try:
            json_data = json.loads(
                selector.css('script:contains("propertyData")::text').re_first(r'window.PAGE_MODEL = (.*)')).get(
                'propertyData', {})
        except Exception as e:
            json_data = {}
            error = f'Error parsing JSON data for URL {url}: {e} \n\n'
            print(error)

        images, images_urls, floor_plan = get_images(selector)

        item = OrderedDict()
        address = selector.css('[itemprop="streetAddress"]::text').get(default='').strip()
        item['Address'] = address
        item['Price PCM'] = selector.css('article div span:contains(" pcm")::text').get(default='').replace('pcm', '').strip()
        item['Price PW'] = selector.css('article div:contains("pw")::text').get(default='').replace('pw', '').strip()
        item['Property Type'] = get_value_by_heading(selector, 'PROPERTY TYPE') or json_data.get('propertySubType', '')
        item['Bedrooms'] = get_value_by_heading(selector, 'BEDROOMS') or str(json_data.get('bedrooms', ''))
        item['Bathrooms'] = get_value_by_heading(selector, 'BATHROOMS') or str(json_data.get('bathrooms', ''))
        item['Available Date'] = get_value_by_heading(selector, 'Let available date:', letting_details=True)
        item['Furnish Type'] = get_value_by_heading(selector, 'Furnish type:', letting_details=True)
        item['image_urls'] = images_urls
        item['Floor Plan image url'] = floor_plan

        item.update(images)

        pdf = make_pdf(item=item, response=selector)
        file_name = slugify(address)

        # Remove 'image_urls' and 'Floor Plan image url' from item
        del item['image_urls']
        del item['Floor Plan image url']

        # Remove keys added by images update
        for key in images.keys():
            del item[key]

        # Add individual images and floor plan to item
        for i in range(1, 11):
            item[f'Image {i}'] = images.get(f'Image {i}', '')
        item['Floor Plan'] = images.get('Floor Plan', '')

        data.append(item)

        print(f'PDf File : {file_name} created against : {url}')
        return pdf, data, file_name, error
    except Exception as e:
        error = f"Error processing URL {url}: {e} \n\n"
        print('Error :', error)
        return '', [], '', error
