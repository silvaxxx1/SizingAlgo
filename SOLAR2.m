clc;
clear;
close all;

%% Constants & Parameters
AD = 5; % Daily average energy demand (kWh)
uinv = 0.9; % Inverter efficiency
dod = 0.6; % Depth of Discharge
Vs = 12; % Battery voltage (V)
eff = 0.9; % Wind turbine efficiency
vr = 3; % Wind turbine rated speed (m/s)
vcut = 25; % Wind cut-off speed (m/s)
pr = 5; % Rated power of wind turbine (kW)
R_grid = 0.2; % Grid reliability factor
convert = 0.85; % Conversion efficiency

%% Optimization Variables
x = [3, 5, 2]; % Example decision variables: x(1) -> Nbat, x(2) -> Nwt, x(3) -> Npv
Nbat = x(1); 
Nwt = x(2); 
Npv = x(3);

%% Load Profile
load wind.mat; % Ensure this file contains 'wind' data
load solar.mat; % Ensure this file contains 'solar' data
load load.mat; % Ensure this file contains 'load' data
T = length(wind); % Simulation time steps

%% Energy Requirements
EL = convert * sum(load); % Energy demand in Wh
Bcap = (AD * EL) / (uinv * Nbat * dod * Vs); % Battery capacity (Wh)

%% Wind Turbine Power Calculation
pwg = zeros(T,1); % Preallocate power array

for t = 1:T
    if vr < wind(t) && wind(t) < vcut
        pwt = pr; % Assign rated power within operational limits
    else
        pwt = 0; % No power outside operational range
    end
    pwg(t) = pwt * eff; % Apply efficiency
end

%% Number of Wind Turbines
Nwt = wind ./ (pwg + eps); % Avoid division by zero

%% Charge Function
function [Eb, LPS, LPSP] = charge(Eb, Ebmax, Pl, Pw, Ps)
    LPS = 0;
    if (Pw + Ps) >= Pl
        Eb = min(Eb + (Pw + Ps - Pl), Ebmax);
    else
        LPS = Pl - (Pw + Ps);
        Eb = max(Eb - LPS, 0);
    end
    LPSP = LPS / Pl; % Loss of power supply probability
end

%% Grid Power Calculation
Grid_p = zeros(T,1);
for t = 1:T
    Grid_p(t) = max(0, load(t) - (pwg(t) + Npv * solar(t))); % Grid power use
end

%% Reliability & Cost
REF = sum(pwg + Npv * solar) / sum(load); % Reliability factor
LPSP = sum(Grid_p) / sum(load); % Loss of Power Supply Probability
Objective = sum(Grid_p .* 0.023) + REF + LPSP; % Cost function

%% Plot Results
figure;
yyaxis left;
plot(1:T, pwg, 'b', 'LineWidth', 1.5);
hold on;
plot(1:T, Npv * solar, 'r', 'LineWidth', 1.5);
ylabel('Power (kW)');
legend('Wind Power', 'Solar Power');

yyaxis right;
plot(1:T, Grid_p, 'g', 'LineWidth', 1.5);
ylabel('Grid Power (kW)');
xlabel('Time (Hours)');
legend('Grid Power');
title('Hybrid Energy System Performance');
grid on;
