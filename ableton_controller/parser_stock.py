"""Parser setup for stock commands."""

from .parser_args import add_device_ref_args, add_registry_arg, add_stock_control_value_args, add_stock_root_arg

def add_stock_commands(sub):
    stock_devices = sub.add_parser("stock-devices", help="List stock Live devices from the explicit controls registry.")
    add_registry_arg(stock_devices)
    add_stock_root_arg(stock_devices)
    stock_devices.add_argument("--query", help="Filter by name, path, class name, or slug.")
    stock_devices.add_argument("--controls", action="store_true", help="Include every explicit control in the listing.")
    stock_devices.add_argument("--summary", action="store_true", help="Only print registry summary counts.")

    stock_controls = sub.add_parser("stock-controls", help="List explicit controls for one stock Live device.")
    add_registry_arg(stock_controls)
    add_stock_root_arg(stock_controls)
    stock_controls.add_argument("--device", required=True, help="Stock device name, path, class name, or slug.")
    stock_controls.add_argument("--control", help="Optional control name, slug, alias, or parameter index.")

    stock_coverage = sub.add_parser("stock-coverage", help="Verify that the stock device controls registry is complete.")
    add_registry_arg(stock_coverage)

    stock_set = sub.add_parser("set-stock-control", help="Set a loaded stock device control by registry alias.")
    add_registry_arg(stock_set)
    add_device_ref_args(stock_set)
    add_stock_root_arg(stock_set)
    stock_set.add_argument("--stock-device", help="Registry device name/path/slug. Defaults to --device when that is a name.")
    stock_set.add_argument("--control", required=True, help="Control name, slug, alias, or parameter index.")
    add_stock_control_value_args(stock_set)
