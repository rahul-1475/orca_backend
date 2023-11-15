from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from orca_nw_lib.mclag import (
    get_mclags,
    del_mclag,
    config_mclag,
    get_mclag_gw_mac,
    del_mclag_gw_mac,
    config_mclag_gw_mac,
    get_mclag_mem_portchnls,
    config_mclag_mem_portchnl,
    del_mclag_member,
)
@api_view(["GET", "PUT", "DELETE"])
def device_mclag_list(request):
    result = []
    http_status = True
    if request.method == "GET":
        device_ip = request.GET.get("mgt_ip", "")
        if not device_ip:
            return Response(
                {"status": "Required field device mgt_ip not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        domain_id = request.GET.get("domain_id", None)
        data = get_mclags(device_ip, domain_id)
        if data and domain_id:
            data["mclag_members"] = get_mclag_mem_portchnls(device_ip, domain_id)
        return JsonResponse(data, safe=False)
    if request.method == "DELETE":
        for req_data in (
            request.data
            if isinstance(request.data, list)
            else [request.data]
            if request.data
            else []
        ):
            device_ip = req_data.get("mgt_ip", "")
            mclag_members = req_data.get("mclag_members", None)

            if not device_ip:
                return Response(
                    {"status": "Required field device mgt_ip not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # If member are given in the request body
            # Delete the members only, otherwise request is considered
            # to be for deleting the MCLAG
            if mclag_members:
                try:
                    del_mclag_member(device_ip)
                    result.append(
                        f"{request.method} MCLAG member deletion successful: {req_data}"
                    )
                except Exception as err:
                    result.append(
                        f"{request.method}  MCLAG member deletion failed: {req_data} {str(err)}"
                    )
                    http_status = http_status and False
            else:
                try:
                    del_mclag(device_ip)
                    result.append(
                        f"{request.method} MCLAG deletion successful: {req_data}"
                    )
                except Exception as err:
                    result.append(
                        f"{request.method}  MCLAG deletion failed: {req_data} {str(err)}"
                    )
                    http_status = http_status and False

    elif request.method == "PUT":
        for req_data in (
            request.data
            if isinstance(request.data, list)
            else [request.data]
            if request.data
            else []
        ):
            device_ip = req_data.get("mgt_ip", "")
            domain_id = req_data.get("domain_id", "")
            src_addr = req_data.get("source_address", "")
            peer_addr = req_data.get("peer_addr", "")
            peer_link = req_data.get("peer_link", "")
            mclag_sys_mac = req_data.get("mclag_sys_mac", "")
            mclag_members = req_data.get("mclag_members", [])

            if not device_ip or not domain_id:
                return Response(
                    {
                        "result": "All of the required fields mgt_ip, domain_id not found."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if src_addr and peer_addr and peer_link and mclag_sys_mac:
                try:
                    config_mclag(
                        device_ip,
                        domain_id,
                        src_addr,
                        peer_addr,
                        peer_link,
                        mclag_sys_mac,
                    )
                    result.append(f"{request.method} request successful: {req_data}")
                except Exception as err:
                    result.append(
                        f"{request.method} request failed: {req_data} {str(err)}"
                    )
                    http_status = http_status and False

            for mem in mclag_members:
                try:
                    config_mclag_mem_portchnl(device_ip, domain_id, mem)
                    result.append(f"{request.method} request successful :\n {mem}")
                except Exception as err:
                    result.append(
                        f"{request.method} request failed :\n {mem} {str(err)}"
                    )

    return Response(
        {"result": result},
        status=status.HTTP_200_OK
        if http_status
        else status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["GET", "PUT", "DELETE"])
def mclag_gateway_mac(request):
    if request.method == "GET":
        device_ip = request.GET.get("mgt_ip", "")
        if not device_ip:
            return Response(
                {"status": "Required field device mgt_ip not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        gateway_mac = request.GET.get("gateway_mac", "")
        data = get_mclag_gw_mac(device_ip, gateway_mac)
        return JsonResponse(data, safe=False)
    if request.method == "DELETE":
        device_ip = request.data.get("mgt_ip", "")
        if not device_ip:
            return Response(
                {"status": "Required field device mgt_ip not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            del_mclag_gw_mac(device_ip)
            return Response(
                {"result": f"{request.method} request successful: {request.data}"},
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                {
                    "result": f"{request.method} request failed: {request.data} {str(err)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    elif request.method == "PUT":
        device_ip = request.data.get("mgt_ip", "")
        if not device_ip:
            return Response(
                {"status": "Required field device mgt_ip not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mclag_gateway_mac = request.data.get("gateway_mac", "")
        if not mclag_gateway_mac:
            return Response(
                {"status": "Required field device mclag_gateway_mac not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            config_mclag_gw_mac(device_ip, mclag_gateway_mac)
            return Response(
                {"result": f"{request.method} request successful: {request.data}"},
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                {
                    "result": f"{request.method} request failed: {request.data} {str(err)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )