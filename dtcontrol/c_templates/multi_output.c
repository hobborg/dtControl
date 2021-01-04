#include <stdio.h>
#include<string.h>
#include<stdlib.h>
void classify(const float x[], float result[]);

int main(int argc, char** argv) {
    float x[{{num_inputs}}];
    for(int i=0;i<{{num_inputs}};i++)
    {
        x[i]=atof(argv[i+1]);
    }
    float result[{{num_outputs}}];
    classify(x, result);
    for(int j=0;j<{{num_outputs}};j++)
    {
        printf("%f", result[j]);
        if (j!=({{num_outputs}}-1))
        {
            printf(",");
        }
    }
    return 0;
}

void classify(const float x[], float result[]) {
{{code}}
}
