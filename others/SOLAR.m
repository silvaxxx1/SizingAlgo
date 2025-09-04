%% battery
Nbat = x(3); % Number of batteries selected by PSO
uinv = 0.95; % Inverter efficiency
dod = 0.8; % Depth of discharge
AD = 3; % Autonomy days
EL = convert; % Load demand
Vs = 48; % Battery voltage
Bcap = AD * EL / uinv * n_bat * dod * Vs; % Battery capacity calculation
SOCmin = xlsread('SOCmin.xlsx', 1, 'A1:A180')'; % Minimum SOC
SOCmax = xlsread('SOCmax.xlsx', 1, 'B1:B180')'; % Maximum SOC

%% solar
solar = xlsread('g.xlsx', 1, 'E19:E8778')'; % Solar irradiance data (W/m^2)
temp = xlsread('g.xlsx', 1, 'F19:F8778')'; % Temperature data (°C)
Tam = temp; % Ambient temperature
Gref = 1000; % Reference solar radiation (W/m^2)
NOCT = 45; % Nominal cell operating temperature
kt = -3.7e-3; % Temperature coefficient
Tref = 25; % Temperature at reference condition
Tc = Tam + ((NOCT - 20) / 800) .* solar; % Cell temperature
pv_eff = 7.3; % Solar panel efficiency
G = solar;
PV_out = (pv_eff .* (G / Gref)) .* (1 + kt .* (Tc - Tref)); % PV output power
pp = PV_out;
figure; plot(pp); axis tight; box on; grid on;
xlabel('Time (hours)'); ylabel('PV output power (kW)'); title('Output power generated from PV');


%% WIND
wind = xlsread('g.xlsx', 1, 'G19:G8778')'; % Wind speed data (m/s)
load('WindTurbines.mat'); % Load wind turbine data
V1 = wind; % Wind speed at reference height
h2 = 70; % Hub height
h1 = 43.6; % Reference height
alfa = 0.25; % Power law exponent for heavily forested landscape
V2 = V1 * (h2 / h1)^(alfa); % Wind speed at hub height
WTM = 4; % Chosen wind turbine model
bd = cell2mat(WindTurbines(WTM, 2)); % Blade diameter (m)
eff = cell2mat(WindTurbines(WTM, 4)); % Efficiency
vcut = cell2mat(WindTurbines(WTM, 5)); % Cut-out speed (m/s)
vin = cell2mat(WindTurbines(WTM, 6)); % Cut-in speed (m/s)
vr = cell2mat(WindTurbines(WTM, 7)); % Rated speed (m/s)
pr = cell2mat(WindTurbines(WTM, 8)); % Rated power (kW)
pcut = cell2mat(WindTurbines(WTM, 9)); % Output power at cut-out speed
pmax = cell2mat(WindTurbines(WTM, 10)); % Maximum output power

for t = 1:1:8760
    if V2(t) < vin
        pwt(t) = 0;
    elseif vin <= V2(t) && V2(t) <= vr
        pwt(t) = ((V2(t))^3 * (pr / ((vr)^3 - (vin)^3))) - pr * ((vin)^3 / ((vr)^3 - (vin)^3));
    elseif vr < V2(t) && V2(t) < vcut
        pwt(t) = 0;
    end
    pwg(t) = pwt(t) * eff; % Electric power from wind turbine
end
Nwt = wind / pwg;
figure; yyaxis right; hold on; plot(pp); hold on; ylabel('PV output power (kW)');
yyaxis left; hold on; plot(pwg); ylabel('Wind turbine output (kW)'); hold off;
axis tight; box on; title('P_p_v & P_w_t'); xlabel('Time (hours)');


%%%%%%%%%%% CHARGE %%%%%%%%%%
function [Eb, Ech, Edch, Egrid_s, Ev] = charge(Eb, Ebmax, Pl, t, Ech, Edch, Pw, Ps, n_bat, Egrid_s, Ev, car_av)
    uconv = 0.95; % Converter efficiency
    uinv = 0.95; % Inverter efficiency
    C_Rate = 7.2; % Battery charge rate (kW/h)
    Evmax = 24; % EV battery capacity
    temp2 = 0; % Temporary variable for charging
    Edch(t) = 0;
    Egrid_s(t) = 0;
    Pch(t) = ((Pw(t) + Ps(t)) * uinv) - (Pl(t) / uinv);
    Ech(t) = Pch(t) .* n_bat .* uconv; % Energy available to battery
    if Ech(t) <= Ebmax - Eb(t - 1)
        Eb(t) = Eb(t - 1) + Ech(t);
        Ev(t) = Ev(t - 1);
    else
        Eb(t) = Ebmax; % Max SOC constraint
        Egrid_s(t) = (Ech(t) - (Ebmax - Eb(t - 1))) / (n_bat); % Energy supplied to grid
        Ech(t) = Ebmax - Eb(t - 1);
        if Egrid_s(t) > C_Rate
            temp1 = C_Rate;
        else
            temp1 = Egrid_s(t);
        end
        Ev(t) = Ev(t - 1);
        if ((Ev(t - 1) <= Evmax) && (car_av(t) == 1)) % Check if EV is at home
            if (temp1 + Ev(t - 1)) > Evmax
                Ev(t) = Evmax;
                temp2 = (Evmax - Ev(t - 1));
                Ech(t) = Ech(t) + temp2;
                Egrid_s(t) = Egrid_s(t) - temp2;
            else
                Ev(t) = Ev(t - 1) + temp1;
                temp2 = temp1;
                Ech(t) = Ech(t) + temp1;
                Egrid_s(t) = Egrid_s(t) - temp1;
            end
        end
    end
end


%% Objective function (1)
Grid_sale = 0.015;
Grid_p = 0.023;
grid_cost = sum(Grid_p) * 0.023 - sum(Grid_sale) * 0.015;
Grid_purchased = sum(Grid_p);
Grid_sale = sum(Grid_sale);
Cgrid = 0.0425 .* Grid_p; % Cost of buying electricity
display(['The value of Cgrid is : ', num2str(Cgrid)]);

%% Objective function (2)
REF = sum(Pw + Ps) ./ sum(Pw + Ps + Grid_purchased); % Renewable Energy Fraction
ref = REF * 100;
GCF = 1 - REF;
display(['The value of REF is : ', num2str(REF)]);
display(['The value of GCF is : ', num2str(GCF)]);

%% Objective function (3)
LPS = (convert - (pp + pwg)) + R_grid;
LPSP = sum(LPS) / sum(convert); % Loss of Power Supply Probability
display(['The value of LPSP is : ', num2str(LPSP)]);



%% Plotting section
figure; yyaxis right; hold on; plot(Ps); hold on; ylabel('PV output power (kW)');
yyaxis left; hold on; plot(Pw); ylabel('Wind turbine output (kW)'); hold off;
axis tight; box on; title('P_p_v & P_w_t'); xlabel('Time (hours)');


