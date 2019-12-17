# SPDX-License-Identifier: GPL-3.0-only
from revvy.utils.functions import is_bit_set

cfsr_reasons = [
    "The processor has attempted to execute an undefined instruction",
    "The processor attempted a load or store at a location that does not permit the operation",
    None,
    "Unstack for an exception return has caused one or more access violations",
    "Stacking for an exception entry has caused one or more access violations",
    "A MemManage fault occurred during floating-point lazy state preservation",
    None,
    None,
    "Instruction bus error",
    "Data bus error (PC value points to the instruction that caused the fault)",
    "Data bus error (PC value is not directly related to the instruction that caused the error)",
    "Unstack for an exception return has caused one or more BusFaults",
    "Stacking for an exception entry has caused one or more BusFaults",
    "A bus fault occurred during floating-point lazy state preservation",
    None,
    None,
    "The processor has attempted to execute an undefined instruction",
    "The processor has attempted to execute an instruction that makes illegal use of the EPSR",
    "The processor has attempted an illegal load to the PC",
    "The processor has attempted to access a coprocessor",
    None,
    None,
    None,
    None,
    "The processor has made an unaligned memory access",
    "The processor has executed an SDIV or UDIV instruction with a divisor of 0",
]


def parse_cfsr(cfsr):
    return [reason for bit, reason in enumerate(cfsr_reasons) if is_bit_set(cfsr, bit) and reason]
