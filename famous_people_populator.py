import asyncio
import csv
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import aiohttp
import requests

import strapi_models as M

types = [
    "ESTJ",
    "ESTP",
    "ENTJ",
    "ENFJ",
    "ESFJ",
    "ESFP",
    "ENTP",
    "ENFP",
    "ISTJ",
    "ISTP",
    "INTJ",
    "INFJ",
    "ISFJ",
    "ISFP",
    "INTP",
    "INFP",
]


def fetch_image_src(name: str) -> Optional[str]:
    api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={name}&prop=pageimages|categories&format=json&pithumbsize=256&cllimit=max"
    try:
        response = requests.get(api_url)
        data = response.json()
        pages = data["query"]["pages"]
        page_id = next(iter(pages))
        page = pages[page_id]
        # Check if the page has a thumbnail
        if "thumbnail" in page:
            return page["thumbnail"]["source"]
        # Define category priorities
        category_priorities = [
            "Living people",
            "Biographies",
            "People",
        ]
        # Check if the page has categories related to people
        categories = page.get("categories", [])
        category_titles = [category["title"] for category in categories]
        # Return the thumbnail image source based on priority
        for priority_category in category_priorities:
            if priority_category in category_titles:
                if "thumbnail" in page:
                    return page["thumbnail"]["source"]
        # If no preferred categories found but a thumbnail exists, return it
        if "thumbnail" in page:
            return page["thumbnail"]["source"]
        return None
    except Exception as error:
        print(f"Error fetching image for {name}:", error)
        return None


def download_file(url: str, name: str) -> str:
    if not url or not name:
        print(f"URL: {url}, Name: {name}")
        raise ValueError("URL and name must be provided")
    fp = f"./images/{name}.jpg"
    curl_command = ["curl", url, "--output", fp]
    subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return fp


async def download_file_async(url: str, name: str, executor: ThreadPoolExecutor) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, download_file, url, name)


def type_to_typeorder(typecode: str) -> int:
    typecode_order = types.index(typecode)
    return typecode_order


async def process_person(person, existing_names, existing_people, executor, semaphore):
    if person.name is None:
        return
    async with semaphore:
        if person.name not in existing_names:
            print(f"Creating {person.name}")
            await person.post()
        else:
            existing_person = [x for x in existing_people if x.name == person.name][0]
            person.picture = existing_person.picture
            print(f"Checking {person.name}")
        if person.picture is None:
            print(f"{person.name} has no picture. Fetching...")
            picture_url = person.picture_url
            if not person.picture_url:
                picture_url = fetch_image_src(person.name)
                if picture_url is None:
                    print(f"Could not find image for {person.name}")
                    return
            print(f"Downloading {person.name}")
            fp = await download_file_async(picture_url, person.name, executor)
            print(f"Uploading {person.name}")
            person.picture = await M.Media.upload_file(fp)
            print(f"Putting {person.name}")
            await person.put()
        else:
            print(f"{person.name} already has a picture")


async def main():
    executor = ThreadPoolExecutor(max_workers=50)
    semaphore = asyncio.Semaphore(50)
    existing_people = await M.FamousPeople.all()
    existing_names = {person.name for person in existing_people}
    with open("./famous.json", "r") as file:
        famous_people = json.load(file)

    tasks = []
    for person in famous_people:
        tasks.append(process_person(person, existing_names, existing_people, executor, semaphore))

    await asyncio.gather(*tasks)
    
if __name__ == "__main__":
    asyncio.run(main())
