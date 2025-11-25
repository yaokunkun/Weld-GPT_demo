WeldWorkSetMode;	                // 焊接方式，MIG/AUTO等，应该没有建表			 
WeldRunSetMode;                    // 运行方式，2T/4T，应该没有建表
WeldPulseSetMode;	              // 脉冲模式，无/单/双脉冲，应该没有建表
MIGMaterialDia; 		            //MIG模式的焊丝直径
MIGMaterialMode;                 //MIG模式下的焊接材料材料
MIGSetMotorSpeed;            //MIG模式下的送丝速度
MIGSetVoltage;              // MIG模式下的设置电压，实际是通过MIGSetVoltageFine来调整
MIGSetInductance ;              // MIG模式下的电子阻抗
MIGSetSinglePluseFrequencyFine;// MIG单脉冲模式下的脉冲频率微调，应该是0~100表示-50%~+50%，通过对一个基值的计算来得到MIGSinglePluseFreque
MIGSetSinglePluseDutyFine; 		        // MIG单脉冲模式下的脉冲占空比微调，应该是0~100表示-50%~+50%，通过对一个基值的计算来得到MIGSinglePluseDuty
MMASetCurrent; 		            //MMA模式下的电流
MMASetHotCurrent;                  // MMA模式下的热电流
MMASetForceCurrent;              //MMA模式下的推力电流
TIGSetPeakCurrent; 		    //TIG模式峰值电流

MIGSetDoublePlusePeakSpeed;        // MIG双脉冲模式下的峰值送丝速度
MIGSetDoublePluseBaseSpeedRatio;        //MIG双脉冲模式下的基值送丝速度
MIGSetDoublePluseFrequency;      //MIG双脉冲模式下的脉冲频率
MIGSetDoublePluseDuty;           //MIG双脉冲模式下的脉冲占空比

MIGSetPreTime;                     // MIG模式下的前气时间
MIGSetStartMotorSpeed;             // MIG模式下的起弧送丝速度
MIGSetUpSlopeTime;                 //MIG模式下的缓升时间
MIGSetDownSlopeTime;               // MIG模式下的缓降时间
MIGSetCraterMotorSpeed;            // MIG模式下的收弧送丝速度
MIGSetPostTime;                    // MIG模式下的后气时间
MIGSetSpotTime;                    // MIG模式下的点焊时间
MIGSetStopTime;                    // MIG模式下的停止时间
MIGMaterialThickness;              //MIG模式下的焊接板厚

MIGSetCurrent;                    // MIG模式下的设置电流，  根据速度计算出来
MIGSetVoltageFine;                // MIG模式下的焊接电压微调


AUTOMaterialMode; 		              // AUTO模式下的材料
AUTOMaterialThickness; 		        // AUTO模式下的焊接板厚
AUTOSetCurrent;                    // AUTO模式下的焊接电流微调 0-100 显示-50% 到 50%

MIGSinglePluseDuty;              // MIG单脉冲模式下的脉冲占空比（显示值）
MIGSinglePluseFreque            // MIG单脉冲模式下的脉冲频率（显示值）