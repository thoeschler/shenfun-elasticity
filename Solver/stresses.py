from shenfun import Function, project, Dx, VectorSpace

def cauchy_stresses(material_parameters, u_hat):
    '''
    Compute components of Cauchy stress tensor.

    Parameters
    ----------
    material_parameters : tuple or list
        Lamé-parameters: (lambd, mu).
    u_hat : shenfun Function
        Displacement field in spectral space.

    Returns
    -------
    T : list
        Cauchy stress Tensor in spectral space.

    '''
    # input assertion
    assert isinstance(material_parameters, tuple)
    for val in material_parameters:
        assert isinstance(val, float)
    assert len(material_parameters) == 2
    assert isinstance(u_hat, Function)
    
    # some parameters
    T_none = u_hat[0].function_space().get_orthogonal()
    dim = len(T_none.bases)
    
    lambd = material_parameters[0]
    mu = material_parameters[1]
    
    # displacement gradient
    H = [ [None for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            H[i][j] = project(Dx(u_hat[i], j), T_none)
    
    # linear strain tensor
    E = [ [None for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            E[i][j] = 0.5 * (H[i][j] + H[j][i])
    
    # trace of linear strain tensor
    trE = 0.
    for i in range(dim):
        trE += E[i][i]
    
    # Cauchy stress tensor
    T = [ [None for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            T[i][j] = 2.0 * mu * E[i][j] 
            if i==j:
                T[i][j] += lambd * trE
            
    return T


def hyper_stresses(material_parameters, u_hat):
    '''
    Compute components of hyper stress tensor.

    Parameters
    ----------
    material_parameters : tuple or list
        (c1, c2, c3, c4, c5).
    u_hat : shenfun Function
        Displacement field in spectral space.

    Returns
    -------
    T : list
        Hyper stress Tensor in spectral space.

    '''
    # input assertion
    assert isinstance(material_parameters, tuple)
    for val in material_parameters:
        assert isinstance(val, float)
    assert len(material_parameters) == 5
    assert isinstance(u_hat, Function)
    
    # some parameters
    T_none = u_hat[0].function_space()

    dim = len(T_none.bases)
 
    c1 = material_parameters[0]
    c2 = material_parameters[1]
    c3 = material_parameters[2]
    c4 = material_parameters[3]
    c5 = material_parameters[4]
    
    # Laplace
    Laplace = [0. for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            Laplace[i] += project(Dx(u_hat[i], j, 2), T_none)
            
    # grad(div(u))
    GradDiv = [0. for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            GradDiv[i] += project(Dx(Dx(u_hat[j], j), i), T_none)
    
    # hyper stresses
    T = [ [ [0. for _ in range(dim)] for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                if i==j:
                    if c2 != 0.:
                        T[i][j][k] += 0.5*c2*Laplace[k]
                    if c3 != 0.:
                        T[i][j][k] += 0.5*c3*GradDiv[k]
                if i==k:
                    if c2 != 0.:
                        T[i][j][k] += 0.5*c2*Laplace[j]
                    if c3 != 0.:
                        T[i][j][k] += 0.5*c3*GradDiv[j]
                if j==k:
                    if c1 != 0.:
                        T[i][j][k] += c1*Laplace[i]
                if c4 != 0.:
                    T[i][j][k] += project(c4*Dx(Dx(u_hat[i], j), k), T_none)
                if c5 != 0.:
                    T[i][j][k] += project(0.5*c5*Dx(Dx(u_hat[j], i), k), T_none) + project(0.5*c5*Dx(Dx(u_hat[k], i), j), T_none)

    return T

def traction_vector_gradient(cauchy_stresses, hyper_stresses, normal_vector):
    '''
    Compute traction vector for linear second order gradient elasticity.

    Parameters
    ----------
    cauchy_stresses : list
        Components of Cauchy stress tensor in spectral space.
    hyper_stresses : list
        Components of hyper stress tensor in spectral space.
    normal_vector : tuple
        Normal vector used to compute the traction.

    Returns
    -------
    t : list
        Traction vector in spectral space.

    '''
    # some paramaters
    dim = len(normal_vector)
    T2 = cauchy_stresses
    T3 = hyper_stresses
    n = normal_vector
    T_none = T2[0][0].function_space()
    
    # compute traction vector
    t = [0. for _ in range(dim)]
    
    # div(T3)
    divT3 = [[0. for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                divT3[i][j] += project(Dx(T3[i][j][k], k), T_none)
                
    # divn(T3), divt(T3)
    divnT3 = [[0. for _ in range(dim)] for _ in range(dim)]
    divtT3 = divT3.copy()
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                for l in range(dim):
                    divnT3[i][j] += ( project(Dx(T3[i][j][k], l), T_none) )*n[k]*n[l]
                    divtT3[i][j] -= ( project(Dx(T3[i][j][k], l), T_none) )*n[k]*n[l]
                    
    # traction vector
    t = Function(VectorSpace([T_none, T_none]))
    for i in range(dim):
        for j in range(dim):
            for k in range(T_none.bases[0].N):
                for m in range(T_none.bases[0].N):
                    t[i][k][m] += (T2[i][j][k][m] - divnT3[i][j][k][m] - 2*divtT3[i][j][k][m])*n[j]
            
    return t