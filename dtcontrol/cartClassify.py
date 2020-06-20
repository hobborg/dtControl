import math

tau = 0.3
omega = 1
ga = 0.0125

lb_x0 = 2.24
ub_x0 = 4.08

a=0.05
ae2=0.005
ae5=0.005
ae=0.0033
ah=0.0036
te=12
th=100

bound_x1 = 2
world_dim_x = 10
steps_beyond_done = None

def f(t, x0, x1): 
    return x1

def g(t, x0, x1,u):
    return (-omega * omega * (math.sin(x0)+u * math.cos(x0))- 2 * ga * x1)

def rungeKutta(x0, y0, z0, x, h, u): 
    # Count number of iterations using step size or 
    # step height h 
    n = (int)((x - x0)/h)  
    # Iterate for number of iterations 
    y = y0 
    z = z0
    # Here y is x0 and z is x1 and x is time(tau)

    for i in range(1, n + 1): 
        # "Apply Runge Kutta Formulas to find next value of y and z"
        k0 = h * f(x0, y, z) 
        l0 = h * g(x0, y, z, u)

        k1 = h * f(x0 + 0.5 * h, y + 0.5 * k0, z + 0.5 * l0) 
        l1 = h * g(x0 + 0.5 * h, y + 0.5 * k0, z + 0.5 * l0, u) 

        k2 = h * f(x0 + 0.5 * h, y + 0.5 * k1, z + 0.5 * l1)
        l2 = h * g(x0 + 0.5 * h, y + 0.5 * k1, z + 0.5 * l1, u) 

        k3 = h * f(x0 + h, y + k2, z + l2)
        l3 = h * g(x0 + h, y + k2, z + l2,  u) 

        # Update next value of y and z
        y = y + (1.0 / 6.0)*(k0 + 2 * k1 + 2 * k2 + k3) 
        z = z + (1.0 / 6.0)*(l0 + 2 * l1 + 2 * l2 + l3) 

        # Update next value of x 
        x0 = x0 + h 
    return y,z

def step(x,u):
    if(len(x)==2):
        x0=float(x[0])
        x1=float(x[1])
        u=float(u[0])
        
        costheta = math.cos(x0) 
        sintheta = math.sin(x0)

        derut = rungeKutta(0,x0,x1,tau,0.01,u)
        x0 = derut[0]
        x1 = derut[1] 
        x=(x0,x1)

        done =  x0 < lb_x0 \
                or x0 > ub_x0 \
                or x1 < -bound_x1 \
                or x1 > bound_x1
        done = bool(done)

        if done:
            print('Pole fell at x0= ',x0,' and x1= ',x1)
        if not done:
            reward = 1.0
        # elif steps_beyond_done is None:
        #     # Pole just fell!
        #     steps_beyond_done = 0
        #     reward = 1.0
        # else:
        #     steps_beyond_done += 1
        #     reward = 0.0

        # newu,path = classify(x0,x1)
        # newu is expected to be an array
        # return x,newu,path,done
        return x
    else:
        x0 = float(x[0])
        x1 = float(x[1])
        x2 = float(x[2])
        x3 = float(x[3])
        x4 = float(x[4])
        x5 = float(x[5])
        x6 = float(x[6])
        x7 = float(x[7])
        x8 = float(x[8])
        x9 = float(x[9])

        dx0=(-a-ae)*x0+a*x1+ae*te
        dx1=(-4*a-ae2-ah*u[0])*x1+a*x0+a*x6+a*x8+a*x2+ae2*te+ah*th*u[0]
        dx2=(-2*a-ae)*x2+a*x1+a*x3+ae*te
        dx3=(-2*a-ae)*x3+a*x2+a*x4+ae*te
        dx4=(-4*a-ae5-ah*u[1])*x4+a*x3+a*x7+a*x5+a*x9+ae5*te+ah*th*u[1]
        dx5=(-a-ae)*x5+a*x4+ae*te
        dx6=(-a-ae)*x6+a*x1+ae*te
        dx7=(-a-ae)*x7+a*x4+ae*te
        dx8=(-a-ae)*x8+a*x1+ae*te
        dx9=(-a-ae)*x9+a*x4+ae*te

        x0 = x0 + dx0
        x1 = x1 + dx1
        x2 = x2 + dx2
        x3 = x3 + dx3
        x4 = x4 + dx4
        x5 = x5 + dx5
        x6 = x6 + dx6
        x7 = x7 + dx7
        x8 = x8 + dx8
        x9 = x9 + dx9

        return (x0,x1,x2,x3,x4,x5,x6,x7,x8,x9)