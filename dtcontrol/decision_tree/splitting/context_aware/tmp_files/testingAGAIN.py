from copy import deepcopy

import sympy as sp
import numpy as np
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit

x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9, x_10, x_11, x_12, x_13, x_14, x_15, x_16, x_17, x_18, x_19, x_20, x_21, x_22, x_23, x_24, x_25, x_26, x_27, x_28, x_29, x_30, x_31, x_32, x_33, x_34, x_35, x_36, x_37, x_38, x_39, x_40, x_41, x_42, x_43, x_44, x_45, x_46, x_47, x_48, x_49, x_50, x_51, x_52, x_53, x_54, x_55, x_56, x_57, x_58, x_59, x_60, x_61, x_62, x_63, x_64, x_65, x_66, x_67, x_68, x_69, x_70, x_71, x_72, x_73, x_74, x_75, x_76, x_77, x_78, x_79, x_80, x_81, x_82, x_83, x_84, x_85, x_86, x_87, x_88, x_89, x_90, x_91, x_92, x_93, x_94, x_95, x_96, x_97, x_98, x_99, x_100 = sp.symbols(
    'x_0 x_1 x_2 x_3 x_4 x_5 x_6 x_7 x_8 x_9 x_10 x_11 x_12 x_13 x_14 x_15 x_16 x_17 x_18 x_19 x_20 x_21 x_22 x_23 x_24 x_25 x_26 x_27 x_28 x_29 x_30 x_31 x_32 x_33 x_34 x_35 x_36 x_37 x_38 x_39 x_40 x_41 x_42 x_43 x_44 x_45 x_46 x_47 x_48 x_49 x_50 x_51 x_52 x_53 x_54 x_55 x_56 x_57 x_58 x_59 x_60 x_61 x_62 x_63 x_64 x_65 x_66 x_67 x_68 x_69 x_70 x_71 x_72 x_73 x_74 x_75 x_76 x_77 x_78 x_79 x_80 x_81 x_82 x_83 x_84 x_85 x_86 x_87 x_88 x_89 x_90 x_91 x_92 x_93 x_94 x_95 x_96 x_97 x_98 x_99 x_100')
c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8, c_9, c_10, c_11, c_12, c_13, c_14, c_15, c_16, c_17, c_18, c_19, c_20, c_21, c_22, c_23, c_24, c_25, c_26, c_27, c_28, c_29, c_30, c_31, c_32, c_33, c_34, c_35, c_36, c_37, c_38, c_39, c_40, c_41, c_42, c_43, c_44, c_45, c_46, c_47, c_48, c_49, c_50, c_51, c_52, c_53, c_54, c_55, c_56, c_57, c_58, c_59, c_60, c_61, c_62, c_63, c_64, c_65, c_66, c_67, c_68, c_69, c_70, c_71, c_72, c_73, c_74, c_75, c_76, c_77, c_78, c_79, c_80, c_81, c_82, c_83, c_84, c_85, c_86, c_87, c_88, c_89, c_90, c_91, c_92, c_93, c_94, c_95, c_96, c_97, c_98, c_99, c_100 = sp.symbols(
    'c_0 c_1 c_2 c_3 c_4 c_5 c_6 c_7 c_8 c_9 c_10 c_11 c_12 c_13 c_14 c_15 c_16 c_17 c_18 c_19 c_20 c_21 c_22 c_23 c_24 c_25 c_26 c_27 c_28 c_29 c_30 c_31 c_32 c_33 c_34 c_35 c_36 c_37 c_38 c_39 c_40 c_41 c_42 c_43 c_44 c_45 c_46 c_47 c_48 c_49 c_50 c_51 c_52 c_53 c_54 c_55 c_56 c_57 c_58 c_59 c_60 c_61 c_62 c_63 c_64 c_65 c_66 c_67 c_68 c_69 c_70 c_71 c_72 c_73 c_74 c_75 c_76 c_77 c_78 c_79 c_80 c_81 c_82 c_83 c_84 c_85 c_86 c_87 c_88 c_89 c_90 c_91 c_92 c_93 c_94 c_95 c_96 c_97 c_98 c_99 c_100')

subs_helper_column = [x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9, x_10, x_11, x_12, x_13, x_14, x_15, x_16, x_17, x_18, x_19, x_20,
                      x_21, x_22, x_23, x_24, x_25, x_26, x_27, x_28, x_29, x_30, x_31, x_32, x_33, x_34, x_35, x_36, x_37, x_38, x_39,
                      x_40, x_41, x_42, x_43, x_44, x_45, x_46, x_47, x_48, x_49, x_50, x_51, x_52, x_53, x_54, x_55, x_56, x_57, x_58,
                      x_59, x_60, x_61, x_62, x_63, x_64, x_65, x_66, x_67, x_68, x_69, x_70, x_71, x_72, x_73, x_74, x_75, x_76, x_77,
                      x_78, x_79, x_80, x_81, x_82, x_83, x_84, x_85, x_86, x_87, x_88, x_89, x_90, x_91, x_92, x_93, x_94, x_95, x_96,
                      x_97, x_98, x_99, x_100]
subs_helper_coef = [c_0, c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8, c_9, c_10, c_11, c_12, c_13, c_14, c_15, c_16, c_17, c_18, c_19, c_20,
                    c_21, c_22, c_23, c_24, c_25, c_26, c_27, c_28, c_29, c_30, c_31, c_32, c_33, c_34, c_35, c_36, c_37, c_38, c_39, c_40,
                    c_41, c_42, c_43, c_44, c_45, c_46, c_47, c_48, c_49, c_50, c_51, c_52, c_53, c_54, c_55, c_56, c_57, c_58, c_59, c_60,
                    c_61, c_62, c_63, c_64, c_65, c_66, c_67, c_68, c_69, c_70, c_71, c_72, c_73, c_74, c_75, c_76, c_77, c_78, c_79, c_80,
                    c_81, c_82, c_83, c_84, c_85, c_86, c_87, c_88, c_89, c_90, c_91, c_92, c_93, c_94, c_95, c_96, c_97, c_98, c_99, c_100]

tmp = "#UNITS Meter Meter Baum Haus"

# checking whether first line contains units
if tmp.startswith("#UNITS"):
    units = tmp.split(" ")[1:]
    converted_units = [str.lower(u) for u in units]

print(converted_units)
print(set(converted_units))
print(converted_units)

x = np.array(
    [[1., 4.6, 1., 3.],
     [1., 4.6, 2., 3.],
     [2., 4., 3., 1.],
     [2., 4., 3., 2.],
     [1., 4., 4., 1.],
     [2., 4., 4., 2.],
     [2., 53., 2., 3.],
     [1., 228., 1., 5.],
     [2., 93., 1., 2.],
     [2., 59., 3., 2.]])


for unit in set(converted_units):
    print(unit)
    converted_x = np.copy(x)
    for index in range(len(converted_units)):
        if converted_units[index] != unit:
            converted_x[:, index] = 0
    print(converted_x)

print(x.shape[1])