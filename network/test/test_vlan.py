"""
This module contains tests for the Interface API.
"""

from rest_framework import status
from network.test.test_common import TestORCA


class TestVlan(TestORCA):
    """
    Test the VLAN API.
    """

    vlan_id = 1
    vlan_name = "Vlan1"

    def test_vlan_config(self):
        """
        Test the VLAN configuration.

        This function tests the VLAN configuration by performing a series of HTTP requests.
        """
        device_ip = self.device_ips[0]

        response = self.del_req("vlan_ip_remove", {"mgt_ip": device_ip, "name": self.vlan_name})
        response = self.del_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )

        self.assertTrue(
            response.status_code == status.HTTP_200_OK
            or any(
                "resource not found" in res.lower() for res in response.json()["result"]
            )
        )

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(response.data)

        response = self.put_req(
            "vlan_config",
            {
                "mgt_ip": device_ip,
                "name": self.vlan_name,
                "vlanid": self.vlan_id,
                "mtu": 9000,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.json()["name"], self.vlan_name)
        self.assertEqual(response.json()["vlanid"], self.vlan_id)
        self.assertEqual(response.json()["mtu"], 9000)

        response = self.del_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )

        self.assertTrue(
            response.status_code == status.HTTP_200_OK
            or any(
                "resource not found" in res.lower() for res in response.json()["result"]
            )
        )

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(response.data)

    def test_vlan_mem_config(self):
        """
        Test the VLAN memory configuration.

        This function performs a series of tests on the VLAN memory configuration. It verifies
        that the configuration can be deleted, retrieved, modified, and deleted again without
        any errors or inconsistencies.

        Parameters:
            self (object): The instance of the test class.

        Returns:
            None
        """
        device_ip = self.device_ips[0]
        ether_1 = self.ether_names[0]
        ether_2 = self.ether_names[1]

        request_body = {
            "mgt_ip": device_ip,
            "name": self.vlan_name,
            "vlanid": self.vlan_id,
            "members": {
                ether_1: "TRUNK",
                ether_2: "ACCESS",
            },
        }

        # Remove Vlan.
        self.del_req(
            "device_interface_list",
            {"mgt_ip": device_ip, "name": ether_1, "ifmode": "ACCESS"},
        )
        self.del_req(
            "device_interface_list",
            {"mgt_ip": device_ip, "name": ether_1, "ifmode": "TRUNK"},
        )
        self.del_req(
            "device_interface_list",
            {"mgt_ip": device_ip, "name": ether_2, "ifmode": "ACCESS"},
        )
        self.del_req(
            "device_interface_list",
            {"mgt_ip": device_ip, "name": ether_2, "ifmode": "TRUNK"},
        )

        # Delete VLAN members.
        response = self.del_req("vlan_mem_delete", request_body)
        self.assertTrue(
            response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        )
        # Confirm deletion of VLAN members.
        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertTrue(
            response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        )

        # Now delete VLAN
        response = self.del_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )

        self.assertTrue(
            response.status_code == status.HTTP_200_OK
            or any(
                "resource not found" in res.lower() for res in response.json()["result"]
            )
        )

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(response.data)

        response = self.put_req(
            "vlan_config",
            request_body,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.json()["name"], self.vlan_name)
        self.assertEqual(response.json()["vlanid"], self.vlan_id)
        self.assertTrue(
            all(
                True if m in response.json()["members"] else False
                for m in response.json()["members"]
            )
        )
        self.assertEqual(response.json()["members"][ether_1], "tagged")
        self.assertEqual(response.json()["members"][ether_2], "untagged")

        # Delete VLAN members.
        response = self.del_req("vlan_mem_delete", request_body)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Confirm deletion of VLAN members.
        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(set(response.json()["members"]) & set(request_body["members"].keys()))

        ## Delete VLAN
        response = self.del_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.status_code == status.HTTP_200_OK
            or any(
                "resource not found" in res.lower() for res in response.json()["result"]
            )
        )

        response = self.get_req(
            "vlan_config", {"mgt_ip": device_ip, "name": self.vlan_name}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(response.data)