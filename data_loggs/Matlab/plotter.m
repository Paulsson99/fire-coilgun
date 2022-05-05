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
title('Kulans startposition relativt utgångshastighet för olika spolar')
xlabel('Kulans startposition [mm]')
ylabel('Utgångshastighet [m/s]')
cd ../..

%%


