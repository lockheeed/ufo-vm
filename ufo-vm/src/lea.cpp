#include <stdint.h>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

extern void* data_base;

void* _lea(int instr_type, int size, void* entry)
{
	short op_1 = *(short*)PTR_SUM(entry, 1);
	void* op_2 = PTR_SUM(entry, 3);
	*(uint16_t*)PTR_SUM(data_base, op_1) = *(uint16_t*)op_2;
	return PTR_SUM(entry, 5);
}