import math

tau = 0.3
omega = 1
ga = 0.0125

lb_x0 = 2.24
ub_x0 = 4.08

bound_x1 = 2
world_dim_x = 10
steps_beyond_done = None

def classify(x0,x1):
    dumstr = ""

    x0 = float(x0)
    x1 = float(x1)
    
    x0*=100
    x0=math.floor(x0)
    x0-=224
    quo = math.floor(x0/8)
    x0= 2.24+0.08*quo

    x1*=10
    x1=math.floor(x1)
    x1/=10

    # print('####################x0 is',x0,' and x1 is ',x1)

    if (x1 <= -0.05):
        dumstr="0"
        if (x0 <= 3.64):
            dumstr+="0"
            if (x1 <= -0.35):
                dumstr+="0"
                if (x0 <= 3.56):
                    dumstr+="0"
                    return 4.0,dumstr

                else :
                    dumstr+="1"
                    return 0.6,dumstr

            else :
                dumstr+="1"
                if (x0 <= 2.36):
                    dumstr+="0"
                    return 3.9,dumstr
                else :
                    dumstr+="1"
                    return 2.0,dumstr

        else :
            dumstr+="1"
            if (x1 <= -1.85):
                dumstr+="0"
                return 0.3,dumstr

            else :
                dumstr+="1"
                if (x1 <= -0.15):
                    dumstr+="0"
                    return 0.0,dumstr

                else :
                    dumstr+="1"
                    return -0.8,dumstr

    else :
        dumstr+="1"
        if (x0 <= 2.76):
            dumstr+="0"
            if (x1 <= 0.15):
                dumstr+="0"
                return 1.8,dumstr

            else :
                dumstr+="1"
                if (x1 <= 0.25) :
                    dumstr+="0"
                    return 0.0,dumstr

                else :
                    dumstr+="1"
                    return -0.6,dumstr

        else :
            dumstr+="1"
            if (x1 <= 0.15) :
                dumstr+="0"
                if (x0 <= 2.84) :
                    dumstr+="0"
                    return 0.0,dumstr

                else :
                    dumstr+="1"
                    return -3.0,dumstr

            else :
                dumstr+="1"
                return -4.0,dumstr

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
    x0, x1= x
    x0=float(x0)
    x1=float(x1)
    u=float(u)
    
    costheta = math.cos(x0) 
    sintheta = math.sin(x0)

    # u = classify(x0,x1)

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

    newu,path = classify(x0,x1)

    return x,newu,path,done