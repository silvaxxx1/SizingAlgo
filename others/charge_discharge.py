def charge(Eb, Ebmax, Pl, t, Ech, Edch, Pw, Ps, n_bat, Egrid_s, Ev, car_av):
    uconv = 0.95  # CONVERTER efficiency
    uinv = 0.95  # inverter efficiency
    C_Rate = 7.2  # battery charge rate kw/h
    Evmax = 24  # capacity of EV BATTERY
    temp2 = 0  # temporary variable 2 STARTING CHARGING CASE
    
    Edch[t] = 0
    Egrid_s[t] = 0
    Pch = ((Pw[t] + Ps[t]) * uinv) - (Pl[t] / uinv)
    Ech[t] = Pch * n_bat * uconv  # The energy available to battery
    
    if Ech[t] <= Ebmax - Eb[t-1]:
        Eb[t] = Eb[t-1] + Ech[t]
        Ev[t] = Ev[t-1]
    else:
        Eb[t] = Ebmax  # max SOC constraint
        Egrid_s[t] = (Ech[t] - (Ebmax - Eb[t-1])) / (n_bat)  # energy supplied to grid
        Ech[t] = Ebmax - Eb[t-1]
        
        if Egrid_s[t] > C_Rate:
            temp1 = C_Rate
        else:
            temp1 = Egrid_s[t]
        
        Ev[t] = Ev[t-1]
        
        if (Ev[t-1] <= Evmax) and (car_av[t] == 1):
            if (temp1 + Ev[t-1]) > Evmax:
                Ev[t] = Evmax
                temp2 = (Evmax - Ev[t-1])
                Ech[t] = Ech[t] + temp2
                Egrid_s[t] = Egrid_s[t] - temp2
            else:
                Ev[t] = Ev[t-1] + temp1
                temp2 = temp1
                Ech[t] = Ech[t] + temp1
                Egrid_s[t] = Egrid_s[t] - temp1
    
    return Eb, Ech, Edch, Egrid_s, Ev

def discharge(Pw, Ps, Eb, Ebmax, Pl, t, Ebmin, Edch, Ech, Egrid_p, Ev, car_av):
    uconv = 0.95
    uinv = 0.95
    
    Pdch = (Pl[t] / uinv) - ((Pw[t] + Ps[t]) * uconv)
    Edch[t] = Pdch * 1  # one hour iteration time
    Ech[t] = 0
    Egrid_p[t] = 0
    D_Rate = 7.2  # battery discharge rate
    Evmax = 24
    temp1 = 0
    
    if (Ev[t-1] < (Evmax * 0.2)) and (car_av[t] == 1):
        if (Eb[t-1] - Edch[t]) >= Ebmin:
            Eb[t] = Eb[t-1] - Edch[t]
        else:
            Eb[t] = Ebmin
            Edch[t] = Eb[t-1] - Ebmin
    else:
        Eb[t] = Eb[t-1] - Edch[t]
        
    return Eb, Ech, Edch, Egrid_p, Ev
