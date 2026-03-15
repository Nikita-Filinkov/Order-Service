import asyncio
from pprint import pprint

from app.services.catalog_service.infrastructure.catalog import CatalogClient


async def main():
    catalog = CatalogClient()
    try:
        await catalog.check_availability()
        result = await catalog.get_item_by_id(
            item_id="0a4db214-e0e7-484e-9a9a-287546247b17"
        )
        pprint(result)
    finally:
        await catalog.close()


if __name__ == "__main__":
    asyncio.run(main())
