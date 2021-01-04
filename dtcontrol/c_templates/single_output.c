#include <stdio.h>
#include<string.h>
#include<stdlib.h>
float classify(const float x[]);
int main(int argc, char** argv)
{
    float x[{{num_inputs}}];
    for(int i=0;i<{{num_inputs}};i++)
    {
        x[i]=atof(argv[i+1]);
    }
    float result=classify(x);
    printf("%f", result);
    return 0;
}
float classify(const float x[])
{
{{code}}
}
