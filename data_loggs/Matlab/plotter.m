% Code to plot figures from data, OBS kaos copy pasta 

%% Plotta startposition utgånshastighet

cd 1st_coil/200_2
data1 = [];
files = dir('*.csv');
for i=1:length(files)
    data1 = [data1; load(files(i).name, '-ascii')];
end
cd ../250_2
data2 = [];
files = dir('*.csv');
for i=1:length(files)
    data2 = [data2; load(files(i).name, '-ascii')];
end
cd ../250_3
data3 = [];
files = dir('*.csv');
for i=1:length(files)
    data3 = [data3; load(files(i).name, '-ascii')];
end



[~,idx] = unique(data1(:,6));
data1 = data1(idx,:);

[~,idx] = unique(data2(:,6));
data2 = data2(idx,:);


[~,idx] = unique(data3(:,6));
data3 = data3(idx,:);

plot(data1(:,6), data1(:,2), '*-');
hold on
plot(data2(:,6), data2(:,2), 'o-');
hold on
plot(data3(:,6), data3(:,2), '.-');

hold on
legend({'2 cm spole 200 varv', '2 cm spole 250 varv', '3 cm spole 250 varv'})
title('Kulans startposition relativt utgångshastighet för första spolen')
xlabel('Kulans startposition [mm]')
ylabel('Utgångshastighet [m/s]')
cd ../..

%% coil 2


cd 2nd_coil/200_3
data1 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data1 = [data1; tmp(2,:)];
end
cd ../150_3
data2 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data2 = [data2; tmp(2,:)];
end


[~,idx] = unique(data1(:,6));
data1 = data1(idx,:);

[~,idx] = unique(data2(:,6));
data2 = data2(idx,:);


plot(data1(:,6), data1(:,2), '*-');
hold on
plot(data2(:,6), data2(:,2), 'o-');
hold on
legend({'3 cm spole 200 varv', '3 cm spole 150 varv'})
title('Utgångshastighet relativt spolens placering för andra spolen')
xlabel('Avstånd mellan spolen och sensorn [mm]')
ylabel('Utgångshastighet [m/s]')
cd ../..

%% coil 3


cd 3rd_coil/150_3
data1 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data1 = [data1; tmp(3,:)];
end
cd ../150_5
data2 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data2 = [data2; tmp(3,:)];
end


[~,idx] = unique(data1(:,6));
data1 = data1(idx,:);

[~,idx] = unique(data2(:,6));
data2 = data2(idx,:);


plot(data1(:,6), data1(:,2), '*-');
hold on
plot(data2(:,6), data2(:,2), 'o-');
hold on
legend({'3 cm spole 150 varv', '5 cm spole 150 varv'})
title('Utgångshastighet relativt spolens placering för tredje spolen')
xlabel('Avstånd mellan spolen och sensorn [mm]')
ylabel('Utgångshastighet [m/s]')
cd ../..

%% coil 4



cd 4th_coil/150_4
data1 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data1 = [data1; [tmp(4,1:5) tmp(1,6:7)]];
end
cd ../100_2
data2 = [];
files = dir('*.csv');
for i=1:length(files)
    tmp = load(files(i).name, '-ascii');
    data2 = [data2; [tmp(4,1:5) tmp(1,6:7)]];
end


[~,idx] = unique(data1(:,6));
data1 = data1(idx,:);

[~,idx] = unique(data2(:,6));
data2 = data2(idx,:);


plot(data1(:,6), data1(:,2), '*-');
hold on
plot(data2(:,6), data2(:,2), 'o-');
hold on
legend({'4 cm spole 150 varv', '2 cm spole 100 varv'})
title('Utgångshastighet relativt spolens placering för fjärde spolen')
xlabel('Avstånd mellan spolen och sensorn [mm]')
ylabel('Utgångshastighet [m/s]')
cd ../..

%% coil 7
data1= csvread('7th_coil/7_53.65.csv');
v = [0 ;  data1(:,2)];
dv = v(2:8)-v(1:7);

T = v.^2;
dT = T(2:8)-T(1:7);

plot(data1(:,1)+1, data1(:,2),'*-');
hold on
bar(data1(:,1)+1, dv,0.1)
%hold on
%bar(data1(:,1)+1, dT,0.2)
legend({'Hastighet efter varje spole', 'Hastighetsökning efter varje spole'},'Location','northwest')
title('Kulans hastighet efter varje spole vid 7 spolar')
xlabel('Spole')
ylabel('Hastighet [m/s]')


%% coil 8

data1= csvread('8th_coil/8_54.32.csv');
v = [0 ;  data1(:,2)];
dv = v(2:9)-v(1:8);

T = v.^2;
dT = T(2:9)-T(1:8);

plot(data1(:,1)+1, data1(:,2),'*-');
hold on
bar(data1(:,1)+1, dv,0.1)
%hold on
%bar(data1(:,1)+1, dT,0.2)
legend({'Hastighet efter varje spole', 'Hastighetsökning efter varje spole'},'Location','northwest')
title('Kulans hastighet efter varje spole vid 8 spolar')
xlabel('Spole')
ylabel('Hastighet [m/s]')

