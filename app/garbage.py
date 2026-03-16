import asyncio
from pprint import pprint

from app.services.catalog_service.infrastructure.catalog import CatalogClient


async def main():
    catalog = CatalogClient()
    try:
        await catalog.check_availability()
        result = await catalog.get_item_by_id(
            item_id="67d6b0b0-cbc9-4570-bd4e-75594fcdda2e"
        )
        pprint(result)
    finally:
        await catalog.close()


if __name__ == "__main__":
    asyncio.run(main())
