---
tecnologia: CUDA
categoria: computacao
url_fonte: https://developer.nvidia.com/blog/even-easier-introduction-cuda
titulo: An Even Easier Introduction to CUDA
---

CUDA C++ e apenas uma das formas de criar aplicacoes massivamente paralelas com CUDA. Ela permite usar a linguagem C++ para desenvolver algoritmos de alto desempenho acelerados por milhares de threads paralelas rodando em GPUs.

A transformacao de codigo de CPU para GPU exige converter funcoes no que a terminologia CUDA chama de kernels. Um kernel e uma funcao projetada para rodar no hardware da GPU. Para declarar um kernel basta adicionar o especificador __global__ a funcao, o que informa ao compilador CUDA C++ que aquela funcao roda na GPU e pode ser chamada a partir de codigo de CPU. Codigo que roda em GPUs e chamado de device code, enquanto codigo que executa em CPUs e host code.

Antes que kernels possam computar, e preciso alocar memoria acessivel pela GPU. O Unified Memory em CUDA facilita isso fornecendo um unico espaco de memoria acessivel por todas as GPUs e CPUs do sistema. Em vez de gerenciar espacos de memoria separados para host e device, chama-se cudaMallocManaged() para alocar arrays acessiveis tanto da CPU quanto da GPU. A funcao retorna um ponteiro utilizavel em todo o programa; ao final, cudaFree() libera essa memoria, assim como delete faria em C++ padrao.

Executar um kernel exige uma sintaxe especial, distinta de uma chamada normal de funcao: CUDA usa colchetes angulares triplos para especificar parametros de execucao, como em add<<<1, 1>>>(N, sum, x, y). Os numeros dentro dos colchetes representam a configuracao de execucao que controla a paralelizacao. Lancar com <<<1, 1>>> cria apenas uma thread, executando o kernel sequencialmente. Uma consideracao crucial e que lancamentos de kernel nao bloqueiam a thread da CPU que os chamou: o host continua rodando imediatamente apos o lancamento, e por isso e preciso chamar cudaDeviceSynchronize() para esperar a conclusao do kernel antes de a CPU acessar os resultados.

Para distribuir trabalho entre threads paralelas, os kernels precisam saber qual thread esta executando e quantas threads existem no total. CUDA fornece variaveis embutidas para isso: threadIdx.x retorna o indice da thread dentro do seu block, blockDim.x contem o tamanho do block, blockIdx.x retorna o indice do block dentro do grid e gridDim.x contem o numero total de blocks. A formula idiomatica de indexacao combina esses elementos: blockIdx.x * blockDim.x + threadIdx.x produz um indice global unico para cada thread do grid.

Kernels mais sofisticados usam o padrao grid-stride loop para lidar com conjuntos maiores: int index = blockIdx.x * blockDim.x + threadIdx.x; int stride = blockDim.x * gridDim.x; for (int i = index; i < n; i += stride) y[i] = x[i] + y[i]. Cada thread comeca no indice atribuido e processa cada n-esimo elemento, onde n e o numero total de threads, garantindo que todos os dados sejam processados mesmo quando a contagem de threads nao divide o array perfeitamente.

O artigo demonstra o uso do NSight Systems, invocado pelo comando nsys, para fazer profiling de aplicacoes CUDA. A versao com uma unica thread levou cerca de 91 milhoes de nanossegundos para a soma de um milhao de elementos. Adicionar 256 threads por block reduziu para cerca de 2 milhoes de nanossegundos, um speedup de aproximadamente 45 vezes. Estender para multiplos blocks melhorou para cerca de 47.520 nanossegundos, atingindo um speedup total da ordem de 1.900 vezes.

O prefetch explicito com cudaMemPrefetchAsync() garante que os dados estejam na GPU antes de o kernel precisar deles, evitando falhas de pagina custosas, ja que o Unified Memory em CUDA e memoria virtual cujas paginas migram sob demanda entre os dispositivos. A versao com uma unica thread atingiu apenas 137 megabytes por segundo de largura de banda; a versao de um block com 256 threads chegou a 6 gigabytes por segundo; e a versao otimizada com multiplos blocks e prefetch atingiu 265 gigabytes por segundo, acima de oitenta por cento do pico de 320 gigabytes por segundo da GPU.
