void classify(const float x[], float result[]);

int main(int argc, char** argv) {
    printf("Executing the compiled file");
    printf("Program name is: %s" , argv[0]);
    float x[];
    for(int i=0;i<argc;i++)
    {
        x[i]=atof(argv[i+1]);
    }
    float result[{{num_outputs}}];
    classify(x, result);
    return 0;
}

void classify(const float x[], float result[]) {
{{code}}
}
