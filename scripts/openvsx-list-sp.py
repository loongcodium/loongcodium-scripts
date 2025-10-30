# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "anyio",
#     "httpx",
# ]
# ///
import httpx
from anyio import run, create_task_group
from argparse import ArgumentParser
import json


def get_args():
    parser = ArgumentParser(
        description="Get a list of top target-specific extensions from Open VSX"
    )
    parser.add_argument("-s", "--size", default=10, help="default: %(default)s")
    parser.add_argument("-f", "--offset", default=0, help="default: %(default)s")
    parser.add_argument(
        "-r",
        "--sort-by",
        default="relevance",
        help="default: %(default)s",
        choices=["relevance", "timestamp", "downloadCount", "rating"],
    )
    parser.add_argument("-o", "--output", help="output filename (JSON)")
    return parser.parse_args()


async def fetch_list(
    client: httpx.AsyncClient, size, offset=0, sort_by="relevance", sortOrder="desc"
):
    url = "https://open-vsx.org/api/-/search"
    r = await client.get(
        url,
        params={
            "size": size,
            "offset": offset,
            "sortBy": sort_by,
            "sortOrder": sortOrder,
        },
        follow_redirects=True,
    )
    return r.json()


async def remove_if_target_sp(client: httpx.AsyncClient, ext, ext_list: list):
    r = await client.get(ext["url"])
    if r.status_code != 200:
        # Stop on 429 etc.
        raise Exception(r.status_code, r.content)
    if r.json()["targetPlatform"] == "universal":
        ext_list.remove(ext)


async def main(size=10, offset=0, sort_by="relevance", output=None):
    async with (
        httpx.AsyncClient(limits=httpx.Limits(max_connections=5)) as client,
        create_task_group() as tg,
    ):
        ext_list = (
            await fetch_list(client, size=size, offset=offset, sort_by=sort_by)
        )["extensions"]

        for ext in ext_list:
            tg.start_soon(remove_if_target_sp, client, ext, ext_list)

    if output:
        with open(output, "w") as f:
            json.dump(ext_list, f, indent=2)
    else:
        print(json.dumps(ext_list, indent=2))


if __name__ == "__main__":
    args = get_args()
    run(main, args.size, args.offset, args.sort_by, args.output)
