import asyncio
from pprint import pprint

from app.orders.catalog_service.infrastructure.catalog import CatalogClient


async def main():
    catalog = CatalogClient()
    # result = await catalog.get_item_by_id(
    #     item_id="d4448252-3843-47cb-8ae2-509e603ce407"
    # )
    try:
        result = await catalog.check_availability()
        pprint(result)
    finally:
        await catalog.close()


if __name__ == "__main__":
    asyncio.run(main())
