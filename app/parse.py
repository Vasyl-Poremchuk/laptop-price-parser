import csv
import os.path
from dataclasses import dataclass, fields, astuple
from pprint import pprint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from user_agent import get_random_header, USER_AGENT_LIST

BASE_URL = "https://hotline.ua/"
LAPTOP_URL = urljoin(
    BASE_URL, "ua/computer/noutbuki-netbuki/33373/",
)
OUTPUT_CSV_PATH = "laptops.csv"


@dataclass
class Laptop:
    model: str
    description: str
    min_price: int
    avr_price: int
    max_price: int


LAPTOP_FIELDS = [field.name for field in fields(Laptop)]


def parse_single_laptop(laptop_soup: Tag) -> Laptop:
    """
    Returns an instance of the class `Laptop` with the parsed data
    """
    model = laptop_soup.select_one(".text-md").text.strip()
    list_values = laptop_soup.select_one(
        ".list-item__specifications-text"
    ).text.split("•")[:12]
    description = " / ".join(value.strip() for value in list_values)

    range_price = laptop_soup.select_one(".m_b-5 > .text-sm")
    if range_price:
        range_price = range_price.text.strip().split(" – ")

    avr_price = laptop_soup.select_one(".price__value")
    if avr_price:
        avr_price = int(
            "".join(symbol for symbol in avr_price.text if symbol.isdigit())
        )

    min_price = 0
    max_price = 0

    if range_price and len(range_price) == 2:
        min_price = int(
            "".join(symbol for symbol in range_price[0] if symbol.isdigit())
        )
        max_price = int(
            "".join(symbol for symbol in range_price[1] if symbol.isdigit())
        )

    return Laptop(
        model=model,
        description=description,
        min_price=min_price,
        avr_price=0 if not avr_price else avr_price,
        max_price=max_price,
    )


def get_num_pages(page_soup: Tag) -> int:
    """
    Returns the number of pages in the selected site category
    """
    pagination = page_soup.select_one("div.pagination__pages")

    if pagination is None:
        return 1

    return int(pagination.select("a.page")[-1].text)


def get_single_page_laptops(page_soup: Tag) -> [Laptop]:
    """
    Returns a list of all instances of a class `Laptop` from a single web page
    """
    laptops = page_soup.select(".list-item--row")

    return [parse_single_laptop(laptop_soup) for laptop_soup in laptops]


def get_laptops() -> [Laptop]:
    """
    Returns a list of all instances of the class `Laptop`
    """
    headers = get_random_header(USER_AGENT_LIST)
    page = requests.get(LAPTOP_URL, headers=headers).content
    first_page_soup = BeautifulSoup(page, "html.parser")

    num_pages = get_num_pages(first_page_soup)

    all_laptops = get_single_page_laptops(first_page_soup)

    for page_num in range(2, num_pages + 1):
        page = requests.get(
            LAPTOP_URL, {"p": page_num}, headers=headers,
        ).content
        soup = BeautifulSoup(page, "html.parser")
        all_laptops.extend(get_single_page_laptops(soup))

    return all_laptops


def write_laptops_to_csv(laptops: [Laptop]) -> None:
    """
    The function writes the parsed data to a `laptops.csv` file
    """
    with open(
            OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(LAPTOP_FIELDS)
        writer.writerows([astuple(laptop) for laptop in laptops])


def update_laptop_csv_file(laptops: [Laptop]) -> None:
    """
    The function updates the data of the `laptops.csv` file
    and displays the data of the field that was updated
    """
    existing_data = []

    with open(
            OUTPUT_CSV_PATH, "r", newline="", encoding="utf-8",
    ) as file:
        reader = csv.reader(file)
        for row in reader:
            existing_data.append(row)

    current_data = []

    for laptop in laptops:
        current_data.append(
            [
                str(laptop.model),
                str(laptop.description),
                str(laptop.min_price),
                str(laptop.avr_price),
                str(laptop.max_price),
            ]
        )

    for cur_data in current_data:
        for ex_data in existing_data[1:]:
            if cur_data[0] == ex_data[0]:
                if cur_data[3] != ex_data[3]:
                    pprint(
                        f"UPDATED DATA: model - {cur_data[0]} "
                        f"average price - {cur_data[3]}"
                    )
                break

    write_laptops_to_csv(laptops)


def main() -> None:
    """
    The function checks if a `laptops.csv` exists.
    If so, then the function calls the `update_laptop_csv_file` function,
    otherwise - `write_laptops_to_csv` function
    """
    laptops = get_laptops()
    file_exists = os.path.exists(OUTPUT_CSV_PATH)

    if file_exists:
        update_laptop_csv_file(laptops)
    else:
        write_laptops_to_csv(laptops)


if __name__ == "__main__":
    main()
