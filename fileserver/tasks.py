import os

from celery import shared_task
from isc_dhcp_leases import IscDhcpLeases

from fileserver import constants
from fileserver.models import DHCPServerDetails
from fileserver.ssh import ssh_client_with_private_key
from log_manager.logger import get_backend_logger
from orca_nw_lib.device import get_device_details
from orca_nw_lib.device_gnmi import get_device_details_from_device

_logger = get_backend_logger()

@shared_task(track_started=True, trail=True, acks_late=True)
def scan_dhcp_leases_task(**kwargs):
    """
    Scan the DHCP leases file and update the DHCPDevices table.
    """
    _logger.info("Scanning DHCP leases file.")
    # delete all DHCP devices before scanning

    scanned_devices = []
    devices = DHCPServerDetails.objects.all()
    if not len(devices):
        return {"message": "failed", "details": "No DHCP devices found"}
    devices_in_db = get_device_details()
    discovered_devices = [device.get("mgt_ip") for device in (devices_in_db if devices_in_db else [])]
    app_directory = os.path.dirname(os.path.abspath(__file__))  # Get the path of the current app
    destination_path = os.path.join(app_directory, 'media/dhcp/dhcpd.leases')
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    for device in devices:
        copy_dhcp_file_to_local(
            ip=device.device_ip,
            username=device.username,
            source_path=constants.dhcp_leases_path,
            destination_path=destination_path
        )
        leases = IscDhcpLeases(destination_path)
        for lease in leases.get():
            _logger.debug("Lease: %s", lease)
            if lease.ip not in discovered_devices and "sonic" in lease.hostname:
                _logger.debug(f"Discovered sonic device: {lease.ip} - {lease.hostname}")
                try:
                    device_details = get_device_details_from_device(device_ip=lease.ip)
                    device_details["mgt_ip"] = lease.ip
                    scanned_devices.append(device_details)
                except Exception as e:
                    _logger.error(f"Failed to get device details for {lease.ip}: {e}")
                    scanned_devices.append({
                        "mgt_ip": lease.ip,
                        "mac": lease.ethernet,
                    })
        _logger.info("Scanned DHCP leases file.")

        # Delete the dhcpd.leases local file.
        if os.path.isfile(destination_path):
            os.remove(destination_path)
    return {"sonic_devices": scanned_devices}


def copy_dhcp_file_to_local(ip, username, source_path: str, destination_path: str):
    """
    Copy the specified file from the specified source path to the specified destination path.

    Args:
        ip (str): The IP address of the device.
        username (str): The username to authenticate with the device.
        source_path (str): The source path of the file to copy.
        destination_path (str): The destination path to copy the file to.
    """
    _logger.debug(f"copying file from {source_path} to {destination_path}")
    client = ssh_client_with_private_key(ip, username)
    with client.open_sftp() as sftp:
        sftp.get(source_path, destination_path)
        _logger.debug(f"file copied from {source_path} to {destination_path}")
    client.close()