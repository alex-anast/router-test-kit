# Tests

## Important Note

Normally, `./tests/` contains unit and integration tests for the codebase. In this case, that would be unit tests for the test framework. However, this package does not yet have such tests. It was developed in conjuction with the development of actual integration tests on devices. Therefore, the concept of writing tests for a test framework that tests some code seemed a bit too far-fetched.

Of course, if this test framework is scaled and used in other projects, it would be a good idea to write tests for it.

This directory contains the integration tests that are run on actual router code, specifically for IPSEC. They are meant to work with JSON configuration files, from which they retrieve IPs, usernames, passwords etc of either VMs or physical devices. Of course, these configuration files don't exist here, and that's why the tests are not runnable.

However, I will provide a brief overview of the design here, as well as leave the code as is to showcase what is possible to do with this framework.

### File Contents

1. `./test_ipsec.py`
2. `./pytest.ini`
3. `./conftest.py`

### Use of Pytest

Pytest is a famous testing framework in Python, used to run the IPSEC tests here. For more information, [see here](https://docs.pytest.org/en/stable/contents.html).

- `./pytest.ini`: This file contains the configuration for pytest. It specifies the test files to run, the log format, and other settings.

- `./conftest.py`: This file contains the fixtures that are used in the tests. Fixtures are functions that run before and after tests, and can be used to set up the environment for the tests. It was particularly useful for retrieving configuration data from the JSON files. You can notice in `./test_ipsec.py` function `test_ipsec_generic()` the decorators on top, but also the arguments passed to the function. These arguments are the fixtures that are used in the test.

### How the Tests Were Executed

Such examples can be found at the bottom of the file `./test_ipsec.py`. In short, these are pytest-compatible eligible options:

- Execute setup1 from Generic group:
  `python3 -m pytest -m ipsec -k "generic and setup1-"`

- Execute setup1 from both Generic and Algorithms group:
  `python3 -m pytest -m ipsec -k "setup1-"`

- Execute all tests that don't require vm_c and orange keywords (see JSON)
  `python3 -m pytest -m ipsec -k "not vm_c and not orange"`

### Design of test_ipsec.py

It contains the tests for IPSEC. It is divided into two categories: `generic` and `algorithms`. The `generic` category contains tests that are meant to test the basic functionality of IPSEC, while the `algorithms` category contains tests that are meant to test the algorithms used in IPSEC.

The tests can be run on both actual devices and virtual machines. All the tests care about is the IPs to be reachable. Some tests are using a radius server, others require some modifications on the network interfaces of the connected device etc.

Apart from the two main functions, searched by pytest, `test_ipsec_generic` and `test_ipsec_algorithms`, several more have been written:

1. Several `assert` functions that wrap the `assert` keyword in Python. They are used to check the output of the commands run on the devices.
2. Functions starting with `_` are meant to be used only within other helper functions.
3. Although `TelnetConnection` class implements most of the core functionality of the connection and actions, several specifics needed to be written for IPSEC. For this reason, `TelnetConnectionIPSEC` class was created, that inherits from `TelnetConnection` and implements the specific functions needed for IPSEC.

## List of Available Tests for IPSEC

| File Name   | Description                                         | Test Case #                          |
|-------------|-----------------------------------------------------|--------------------------------------|
| [test_ipsec.py](./test_ipsec.py) | Tests for IPSEC. Categories: `generic` and `algorithms`     |         |
| | `generic` ikev1 tunnel with ipsec profile + acl (tos reflect)                                | setup1  |
| | `generic` basic ezvpn setup                                                                  | setup2  |
| | `generic` crypto maps + hostname resolving (tos reflect)                                     | setup3  |
| | `generic` ikev2 tunnel with ipsec profile (tos af13)                                         | setup4  |
| | `generic` ikev1 tunnel with ipsec profile (tos default)                                      | setup5  |
| | `generic` ikev1/ipv6 tunnel with ipsec profile                                               | setup6  |
| | `generic` ikev2 tunnel for Proximus                                                          | setup7  |
| | `generic` ikev1 gre tunnel with ipsec profile                                                | setup8  |
| | `generic` Orange setup                                                                       | setup9  |
| | `generic` ikev1 gre tunnel with ipsec profile + NAT                                          | setup10 |
| | `generic` ezvpn + radius                                                                     | setup11 |
| | `generic` ezvpn host-enhanced + radius                                                       | setup12 |
| | `generic` ikev2 tunnel with ipsec profile + fragmentation                                    | setup13 |
| | `generic` ikev2 + RRI                                                                        | setup14 |
| | `generic` ikev1 tunnel with virtual template                                                 | setup15 |
| | `generic` ezvpn + radius with virtual template                                               | setup16 |
| | `generic` ikev2 tunnel with virtual template                                                 | setup17 |
| | `generic` ikev1 gre tunnel with virtual template                                             | setup18 |
| | `generic` Full Orange setup                                                                  | setup19 |
| | `generic` RRI with virtual templates configured with vrf                                     | setup20 |
| | `generic` Crypto map with isakmp key and local-address loopback (tos default)                | setup21 |
| | `generic` Crypto map with isakmp peer and aggressive-mode (tos af13)                         | setup22 |
| | `generic` mGRE tunnel with ipsec profile and gkm group mode                                  | setup23 |
| | `generic` multiWan interfaces that share the same gkm group mode                             | setup24 |
| | `generic` ikev2 tunnel + ipv4/ipv6 RRI                                                       | setup25 |
| | `generic` crypto map with multiple endpoints                                                 | setup26 |
| | `generic` ikev2 gre tunnel + ipv6 radius attributes                                          | setup27 |
| | `generic` ikev2 gre tunnel + vasi (PRT-73469)                                                | setup28 |
| | `generic` ikev2 tunnel                                                                       | setup29 |
| | `generic` ikev2 tunnel - no cfg exchange request                                             | setup30 |
| | `generic` ikev2 tunnel - address from address pool                                           | setup31 |
| | `generic` dynamic ikev2 tunnel                                                               | setup32 |
| | `generic` ikev2 tunnel - radius                                                              | setup33 |
| | `generic` ikev2 tunnel - no cfg exchange request - radius                                    | setup34 |
| | `generic` ikev2 tunnel - address from address pool - radius                                  | setup35 |
| | `generic` dynamic ikev2 tunnel - radius                                                      | setup36 |
| | `generic` dynamic ikev2 tunnel - no cfg exchange request - radius                            | setup37 |
| | `generic` dynamic ikev2 tunnel - address from address pool - radius                          | setup38 |
| | `generic` dynamic ikev2 tunnel - radius - dynamic template                                   | setup39 |
| | `algorithms` basic test on algorithms                                                        | setup1  |
