/*
	offset kernels
*/

__kernel void geometryFeedback(
	__global float* output,						//float3
	__global const float* inputPos,					//float3
	__global const unsigned int* indices,
	const uint indexCount)
{
	unsigned int id = get_global_id(0);
	if (id >= indexCount) return;
	unsigned int id3 = id*3;
	// If there is an affectMap, use it to get the actual vert id
	const unsigned int positionId = indices[id];
	if (positionId<0) return;
	unsigned int positionOffset = positionId * 3;				// Base positions are float3 when they come in here!
	output[id3] = inputPos[positionOffset];
	output[id3+1] = inputPos[positionOffset+1];
	output[id3+2] = inputPos[positionOffset+2];
}
