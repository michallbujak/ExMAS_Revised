from dataclasses import dataclass


@dataclass
class PoolType:
    SINGLE: int = 1
    FIFO2: int = 20
    LIFO2: int = 21
    TRIPLE: int = 30
    FIFO3: int = 30
    LIFO3: int = 31
    MIXED3: int = 32
    FIFO4: int = 40
    LIFO4: int = 41
    MIXED4: int = 42
    FIFO5: int = 50
    LIFO5: int = 51
    MIXED5: int = 52
    PLUS5: int = 100
