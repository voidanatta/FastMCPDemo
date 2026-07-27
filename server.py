import argparse
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.applications import Starlette
import uvicorn


mcp = FastMCP("fastmcp-demo")


@mcp.tool
def add(a: float, b: float) -> float:
    """两个数相加，自定义加法运算."""
    return a + b + 3


@mcp.tool
def get_customer_info(customer_code: str) -> dict:
    """根据客户编码获取客户信息."""
    return {
        "StatusCode": "SUCCESS",
        "Message": None,
        "RequestId": "3670a24c-bbb7-4983-9d97-371187be680e",
        "Data": {
            "CustomerId": 1444887,
            "CustomerCode": customer_code,
            "CustomerType": "P",
            "ChannelId": 2,
            "FullName": "2026届校招培训考试",
            "BriefName": "校招考试2026",
            "TeamId1": 80,
            "TeamId2": 11,
            "CustomerTeam": "华东大区001/SH-GOV1",
            "EconomicTypeId": 2,
            "EconomicType": "央企",
            "SalesManUserId": 100757,
            "SalesManUserName": "马云",
            "DevelopeManUserId": 100757,
            "DevelopManUserName": "刘强东",
            "CreditScreenshot": "信用信息.png",
            "BusinessScreenshot": "工商信息.png",
            "JudicialRiskScreenshot": "司法风险信息.png",
            "ChannelName": "B网",
            "OfficeAddress": None,
        },
        "Success": True,
        "BusinessCodeMessage": None,
    }


@mcp.tool
def get_customer_receiving_addresses(customer_code: str) -> dict:
    """根据客户编码获取收货地址信息."""
    return {
        "StatusCode": "SUCCESS",
        "Message": None,
        "RequestId": "3cfeec88-e196-401d-9e1b-290818cd05a0",
        "Data": [
            {
                "ReceiverId": 16085358,
                "CompanyFullName": "",
                "CompanyBriefName": "",
                "ContactName": "收货人1",
                "ContactPhone": "",
                "ContactMobile": "12333333333",
                "Fax": "",
                "Zip": "",
                "Address": "黄浦区测试地址1528号3楼",
                "Longitude": 31.22977,
                "Latitude": 121.462365,
                "Remark": "",
                "Status": "A",
                "CustomerId": 1444811,
                "CustomerCode": customer_code,
                "ProvinceId": 2,
                "CityId": 3,
                "DistrictId": 6,
                "ProvinceName": "上海",
                "CityName": "上海市",
                "DistrictName": "黄浦区",
                "IsDefault": "N",
                "DefaultWarehouseId": 0,
                "DefaultLogicalWarehouseId": 0,
                "OperatorID": None,
                "AccountID": 0,
                "EMail": "",
            }
        ],
        "Success": True,
        "BusinessCodeMessage": None,
    }


@mcp.tool
def get_customer_recent_orders(customer_code: str) -> dict:
    """根据客户编码获取最近订单信息."""
    return {
        "StatusCode": "SUCCESS",
        "Message": None,
        "RequestId": "9b6823df-2098-4521-a79d-4a15f7a57ad4",
        "Data": [
            {
                "OrderId": 880012345,
                "OrderNo": "SO202607270001",
                "CustomerCode": customer_code,
                "CustomerName": "2026届校招培训考试",
                "OrderAmount": 1288.50,
                "OrderStatus": "已完成",
                "OrderTime": "2026-07-25 10:32:18",
                "ReceiverName": "收货人1",
                "ReceiverMobile": "12333333333",
                "ReceiverAddress": "上海市黄浦区黄浦区测试地址1528号3楼",
                "Details": [
                    {
                        "LineNo": 1,
                        "ProductCode": "P-100001",
                        "ProductName": "培训教材套装",
                        "Specification": "标准版",
                        "Quantity": 10,
                        "UnitPrice": 88.50,
                        "LineAmount": 885.00,
                    },
                    {
                        "LineNo": 2,
                        "ProductCode": "P-100002",
                        "ProductName": "考试文具包",
                        "Specification": "基础包",
                        "Quantity": 15,
                        "UnitPrice": 26.90,
                        "LineAmount": 403.50,
                    },
                ],
            }
        ],
        "Success": True,
        "BusinessCodeMessage": None,
    }


@mcp.resource("demo://status")
def status() -> dict[str, str]:
    """Return a small health/status resource."""
    return {
        "service": "fastmcp-demo",
        "status": "ok",
    }


@mcp.prompt
def greeting_prompt(name: str = "developer") -> str:
    """Create a simple greeting prompt."""
    return f"Write a short welcome message for {name}."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FastMCP demo server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http", "sse", "streamable-http", "dual"),
        default="dual",
        help="Transport to use.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP host. Use 0.0.0.0 to allow LAN access.",
    )
    parser.add_argument("--port", type=int, default=8000, help="HTTP port.")
    parser.add_argument(
        "--path",
        default=None,
        help="HTTP MCP endpoint path. Defaults to /sse for sse, otherwise /mcp.",
    )
    return parser.parse_args()


def run_dual_http(host: str, port: int) -> None:
    http_app = mcp.http_app(path="/mcp", transport="streamable-http")
    sse_app = mcp.http_app(path="/sse", transport="sse")

    @asynccontextmanager
    async def lifespan(app: Starlette):
        async with http_app.lifespan(app):
            async with sse_app.lifespan(app):
                yield

    app = Starlette(routes=[*http_app.routes, *sse_app.routes], lifespan=lifespan)
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    args = parse_args()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    if args.transport == "dual":
        run_dual_http(args.host, args.port)
        return

    path = args.path or ("/sse" if args.transport == "sse" else "/mcp")

    mcp.run(
        transport=args.transport,
        host=args.host,
        port=args.port,
        path=path,
    )


if __name__ == "__main__":
    main()