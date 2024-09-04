# TESTS

## List of Available Tests

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

## How to Test

For How to Setup the VMs, jump to the corresponding file, based on the table below:

| Test File     | Setup Instructions                                     |
|---------------|--------------------------------------------------------|
| test_ipsec.py | [./configs_ipsec/README.md](./configs_ipsec/README.md) |
