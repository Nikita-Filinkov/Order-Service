import asyncio
from pprint import pprint

from app.services.catalog_service.infrastructure.catalog import CatalogClient


async def main():
    catalog = CatalogClient()
    try:
        await catalog.check_availability()
        result = await catalog.get_item_by_id(
            item_id="b236e92c-2143-4c47-afa3-2c06b1b8798b"
        )
        pprint(result)
    finally:
        await catalog.close()


if __name__ == "__main__":
    asyncio.run(main())
