

/*
*********************************************************************************************************
*
*                                        BOARD SUPPORT PACKAGE
*
*                                     ST Microelectronics STM32F301
*                                              with the
*                                       Digital Welding Board
*
* Filename      : uart.c
* Version       : V1.00
* Programmer(s) : tzw
*********************************************************************************************************
*/

/*
*********************************************************************************************************
*                                             INCLUDE FILES
*********************************************************************************************************
*/
#include <includes.h>
#include  "usart.h" 
#include "rs485.h"
#include "delay.h"
#include "crc16.h"
/*
*********************************************************************************************************
*                                           LOCAL CONSTANTS
*********************************************************************************************************
*/

/* 串口中断接收到数据的长度变量 */
  u8 USART_RX_CNT = 0;
/* 串口中断接收到数据保存的缓冲区 */
 u8 USART2_RX_BUF[64];
/* 用于标识串口接收数据包是否完成标志 */
//static u8 From_Flag = 0;
u8 From_Flag = 0;
/* 通讯标志 主机发送数据后置1 接收到应答后清零 */
u8 RS485Busy = 0;
/* 接收缓存区 */
u8 RS485_RX_BUF[64];  	//接收缓冲,最大64个字节.
/* 用于保存读命令获得的数据 */
u16 ReadDateVal = 0;
extern u16 Reg[];

/*
*********************************************************************************************************
*                                       LOCAL GLOBAL VARIABLES
*********************************************************************************************************
*/

extern  JOB    Job_Data;
extern  MSG    Msg_Key;  
/*
*********************************************************************************************************
*                                          LOCAL DATA TYPES
*********************************************************************************************************
*/

/*
*********************************************************************************************************
*                                            LOCAL TABLES
*********************************************************************************************************
*/
uint8	TXBuff[128];
uint8	RXBuff[128];
uint8	TXBuff_AI[128];
uint8	RXBuff_AI[128];

/*
*********************************************************************************************************
*                                      LOCAL FUNCTION PROTOTYPES
*********************************************************************************************************
*/

/* 发送数据格式备忘TXBuff[]：

 │￣7￣│￣6￣│￣5￣│￣4￣│￣3￣│￣2￣│￣1￣│￣0￣│
 ￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣ 

TXBuff[0] = (765位为编号)000 (43210位为LCM1的显示数据高位);
TXBuff[1] = (765位为编号)001 (43210位为LCM1的显示数据低位);
TXBuff[2] = (765位为编号)010 (43210位为LCM2的显示数据高位);
TXBuff[3] = (765位为编号)011 (43210位为LCM2的显示数据低位);

TXBuff[4] = (765位为编号)100 (4位为实时显示指令,3位为显示屏闪烁指令,210位焊接模式指令);
							  辅助指令1：焊接状态
							  辅助指令2：HOLD状态
TXBuff[5] = (765位为编号)101 (4位为辅助指令1,3位为辅助指令2,210位菜单模式指令);	
							  辅助指令1：检丝（手焊VRD状态）
							  辅助指令2：2T/4T
TXBuff[6] = (765位为编号)110 (4位公英制状态,3位测试状态,210位网压状态指令);	
TXBuff[7] = (765位为编号)111 (4321未使用, 0位传输判断指令);								  			   
*/ 

/*Msg_Uart:
Msg_Uart.WParam:传递按键消息;
Msg_Uart.IParam:传递编码中键消息;
Msg_Uart.TParam:备用;
Msg_Uart.SParam:备用;
*/
               
/*
*********************************************************************************************************
*                                     UART_TXDATA
*
* Description : UART TX DATA Handle.
*
* Arguments   : 100ms调用.
*
* Returns     : None.
*********************************************************************************************************
*/

void USART_DecodeData(void)			            // 
{
		static uint16 UsartCnnt;
		static uint8  i;
//		if (Job_Data.Fg_RX_USART1_Finish == TRUE) 
		{			
			  switch(RXBuff[5])
				{
					  case 1:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.KeyMenuSetMode = RXBuff[2];
									break;
								  case 7:
									   Job_Data.WeldMIGKeySetMode = RXBuff[2];
									break;
								  case 8:
									   Job_Data.WeldTIGKeySetMode = RXBuff[2];
									break;
								  case 9:
									   Job_Data.WeldMMAKeySetMode = RXBuff[2];
									break;
								  case 10:
									   Job_Data.WeldAUTOKeySetMode = RXBuff[2];
									break;
								  case 11:
									   Job_Data.WeldMIGSubKeySetMode = RXBuff[2];
									break;
								  case 12:
									   Job_Data.FgWaterWorkEn = RXBuff[2];
									break;
								  case 13:
									   Job_Data.MIGSinglePluseDuty = RXBuff[2];
									break;
							    default	:
						      break;												
							}
							Job_Data.KeyMenuSetMode	= RXBuff[6];                    // 低位数据
							Job_Data.WeldMIGKeySetMode =  RXBuff[7];	              // 数据2 低位	
					    Job_Data.WeldTIGKeySetMode	= RXBuff[8]; 		            // 高位数据
							Job_Data.WeldMMAKeySetMode	= RXBuff[9];                // 低位数据
							Job_Data.WeldAUTOKeySetMode	= RXBuff[10]; 		          // 高位数据
							Job_Data.WeldMIGSubKeySetMode	= RXBuff[11];             // 低位数据
              Job_Data.FgWaterWorkEn = RXBuff[12];
              Job_Data.MIGSinglePluseDuty = RXBuff[13]; 
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 2:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MIGPanelSetMotorSpeed = RXBuff[2]<<8;
									   Job_Data.MIGPanelSetMotorSpeed |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
									   Job_Data.MIGSetVoltage = RXBuff[2]<<8;
									   Job_Data.MIGSetVoltage |= RXBuff[3];
									break;
								  case 9:
									break;
								  case 10:
									   Job_Data.MIGSetInductance = RXBuff[2]<<8;
									   Job_Data.MIGSetInductance |= RXBuff[3];
									break;
								  case 11:
									break;
								  case 12:
									   Job_Data.MIGSetVoltageFine = RXBuff[2]<<8;
									   Job_Data.MIGSetVoltageFine |= RXBuff[3];
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MIGPanelSetMotorSpeed = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MIGPanelSetMotorSpeed |= RXBuff[7]  ;	              // 数据2 低位	
							Job_Data.MIGSetVoltage = RXBuff[8]<<8; 		            // 高位数据
							Job_Data.MIGSetVoltage |= RXBuff[9]	;                     // 低位数据
							Job_Data.MIGSetInductance	= RXBuff[10] <<8; 		        // 高位数据
							Job_Data.MIGSetInductance	|= RXBuff[11];                // 低位数据
							Job_Data.MIGSetVoltageFine	= RXBuff[12] <<8; 		        // 高位数据
							Job_Data.MIGSetVoltageFine	|=RXBuff[13];               // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 3:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MIGSetSinglePluseFrequencyFine = RXBuff[2]<<8;
									   Job_Data.MIGSetSinglePluseFrequencyFine |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
									   Job_Data.MIGSetSinglePluseDutyFine = RXBuff[2]<<8;
									   Job_Data.MIGSetSinglePluseDutyFine |= RXBuff[3];
									break;
								  case 9:
									break;
								  case 10:
									   Job_Data.MIGMaterialThickness = RXBuff[2]<<8;
									   Job_Data.MIGMaterialThickness |= RXBuff[3];
									break;
								  case 11:
									break;
								  case 12:
							       Job_Data.FgRemControlEn	= RXBuff[2];                  // 低位数据
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MIGSetSinglePluseFrequencyFine = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MIGSetSinglePluseFrequencyFine |= RXBuff[7]  ;	              // 数据2 低位	
							Job_Data.MIGSetSinglePluseDutyFine = RXBuff[8]<<8; 		            // 高位数据
							Job_Data.MIGSetSinglePluseDutyFine |= RXBuff[9]	;                     // 低位数据
							Job_Data.MIGMaterialThickness	= RXBuff[10] <<8; 		        // 高位数据
							Job_Data.MIGMaterialThickness	|= RXBuff[11];                // 低位数据
//							Job_Data.MIGSinglePluseFrequency	= RXBuff[12] <<8; 		        // 高位数据
//							Job_Data.MIGSinglePluseFrequency	|= RXBuff[13];                // 低位数据
							Job_Data.FgRemControlEn	= RXBuff[12];                  // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 4:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MIGSetDoublePlusePeakSpeed = RXBuff[2]<<8;
									   Job_Data.MIGSetDoublePlusePeakSpeed |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
									   Job_Data.MIGSetDoublePluseBaseSpeedRatio = RXBuff[2]<<8;
									   Job_Data.MIGSetDoublePluseBaseSpeedRatio |= RXBuff[3];
									break;
								  case 9:
									break;
								  case 10:
									   Job_Data.MIGSetDoublePluseFrequency = RXBuff[2]<<8;
									   Job_Data.MIGSetDoublePluseFrequency |= RXBuff[3];
									break;
								  case 11:
									break;
								  case 12:
							       Job_Data.MIGSetDoublePluseDuty	= RXBuff[2] <<8; 		        // 高位数据
							       Job_Data.MIGSetDoublePluseDuty	|=RXBuff[3];               // 低位数据
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MIGSetDoublePlusePeakSpeed = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MIGSetDoublePlusePeakSpeed |= RXBuff[7]  ;	              // 数据2 低位	
							Job_Data.MIGSetDoublePluseBaseSpeedRatio = RXBuff[8]<<8; 		            // 高位数据
							Job_Data.MIGSetDoublePluseBaseSpeedRatio |= RXBuff[9]	;                     // 低位数据
							Job_Data.MIGSetDoublePluseFrequency	= RXBuff[10] <<8; 		        // 高位数据
							Job_Data.MIGSetDoublePluseFrequency	|= RXBuff[11];                // 低位数据
							Job_Data.MIGSetDoublePluseDuty	= RXBuff[12] <<8; 		        // 高位数据
							Job_Data.MIGSetDoublePluseDuty	|=RXBuff[13];               // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 5:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MIGSetPreTime = RXBuff[2]<<8;
									   Job_Data.MIGSetPreTime |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
									   Job_Data.MIGSetPostTime = RXBuff[2]<<8;
									   Job_Data.MIGSetPostTime |= RXBuff[3];
									break;
								  case 9:
									break;
								  case 10:
									   Job_Data.MIGSetSpotTime = RXBuff[2]<<8;
									   Job_Data.MIGSetSpotTime |= RXBuff[3];
									break;
								  case 11:
									break;
								  case 12:
							       Job_Data.MIGSetStopTime	= RXBuff[2] <<8; 		        // 高位数据
							       Job_Data.MIGSetStopTime	|=RXBuff[3];               // 低位数据
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MIGSetPreTime = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MIGSetPreTime |= RXBuff[7]  ;	              // 数据2 低位	
							Job_Data.MIGSetPostTime = RXBuff[8]<<8; 		            // 高位数据
							Job_Data.MIGSetPostTime |= RXBuff[9]	;                     // 低位数据
							Job_Data.MIGSetSpotTime	= RXBuff[10] <<8; 		        // 高位数据
							Job_Data.MIGSetSpotTime	|= RXBuff[11];                // 低位数据
							Job_Data.MIGSetStopTime	= RXBuff[12] <<8; 		        // 高位数据
							Job_Data.MIGSetStopTime	|=RXBuff[13];               // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 6:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MIGSetStartMotorSpeed = RXBuff[2]<<8;
									   Job_Data.MIGSetStartMotorSpeed |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
									   Job_Data.MIGSetUpSlopeTime = RXBuff[2]<<8;
									   Job_Data.MIGSetUpSlopeTime |= RXBuff[3];
									break;
								  case 9:
									break;
								  case 10:
									   Job_Data.MIGSetDownSlopeTime = RXBuff[2]<<8;
									   Job_Data.MIGSetDownSlopeTime |= RXBuff[3];
									break;
								  case 11:
									break;
								  case 12:
							       Job_Data.MIGSetCraterMotorSpeed	= RXBuff[2] <<8; 		        // 高位数据
							       Job_Data.MIGSetCraterMotorSpeed	|=RXBuff[3];               // 低位数据
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MIGSetStartMotorSpeed = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MIGSetStartMotorSpeed |= RXBuff[7]  ;	              // 数据2 低位	
							Job_Data.MIGSetUpSlopeTime = RXBuff[8]<<8; 		            // 高位数据
							Job_Data.MIGSetUpSlopeTime |= RXBuff[9]	;                     // 低位数据
							Job_Data.MIGSetDownSlopeTime	= RXBuff[10] <<8; 		        // 高位数据
							Job_Data.MIGSetDownSlopeTime	|= RXBuff[11];                // 低位数据
							Job_Data.MIGSetCraterMotorSpeed	= RXBuff[12] <<8; 		        // 高位数据
							Job_Data.MIGSetCraterMotorSpeed	|=RXBuff[13];               // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
					  case 7:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.MMASetCurrent = RXBuff[2]<<8;
									   Job_Data.MMASetCurrent |= RXBuff[3];
									break;
								  case 7:
									break;
								  case 8:
						         if((Model_Num	== 354)||(Model_Num	== 504))
										 {
												 Job_Data.MMASetHotCurrentRate = RXBuff[2]<<8;
												 Job_Data.MMASetHotCurrentRate |= RXBuff[3];
										 }
										 else
										 {
												 Job_Data.MMASetHotCurrent = RXBuff[2]<<8;
												 Job_Data.MMASetHotCurrent |= RXBuff[3];
										 }
									break;
								  case 9:
									break;
								  case 10:
						         if((Model_Num	== 354)||(Model_Num	== 504))
										 {
												 Job_Data.MMASetForceCurrentRate = RXBuff[2]<<8;
												 Job_Data.MMASetForceCurrentRate |= RXBuff[3];
										 }
										 else
										 {
												 Job_Data.MMASetForceCurrent = RXBuff[2]<<8;
												 Job_Data.MMASetForceCurrent |= RXBuff[3];
										 }
									break;
								  case 11:
									break;
								  case 12:
							       Job_Data.TIGSetPeakCurrent	= RXBuff[2] <<8; 		        // 高位数据
							       Job_Data.TIGSetPeakCurrent	|=RXBuff[3];               // 低位数据
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.MMASetCurrent = RXBuff[6]<<8;              // 数据1 高位
							Job_Data.MMASetCurrent |= RXBuff[7]  ;	              // 数据2 低位	
						  if((Model_Num	== 354)||(Model_Num	== 504))
						  {
									Job_Data.MMASetHotCurrentRate = RXBuff[8]<<8; 		            // 高位数据
									Job_Data.MMASetHotCurrentRate |= RXBuff[9]	;                     // 低位数据
									Job_Data.MMASetForceCurrentRate	= RXBuff[10] <<8; 		        // 高位数据
									Job_Data.MMASetForceCurrentRate	|= RXBuff[11];                // 低位数据
						  }
						  else
						  {
									Job_Data.MMASetHotCurrent = RXBuff[8]<<8; 		            // 高位数据
									Job_Data.MMASetHotCurrent |= RXBuff[9]	;                     // 低位数据
									Job_Data.MMASetForceCurrent	= RXBuff[10] <<8; 		        // 高位数据
									Job_Data.MMASetForceCurrent	|= RXBuff[11];                // 低位数据
						  }
							
							Job_Data.TIGSetPeakCurrent	= RXBuff[12] <<8; 		        // 高位数据
							Job_Data.TIGSetPeakCurrent	|=RXBuff[13];               // 低位数据
							Msg_Key.EParam = TRUE;	 
						}
						break;
//					  case 8:
//						if(RXBuff[4] == RXBuff[5])//2位校验
//						{
//							Job_Data.LcmCurrentData = RXBuff[6]<<8;              // 数据1 高位
//							Job_Data.LcmCurrentData |= RXBuff[7]  ;	              // 数据2 低位	
//							Job_Data.LcmVoltageData = RXBuff[8]<<8; 		            // 高位数据
//							Job_Data.LcmVoltageData |= RXBuff[9]	;                     // 低位数据
//							Job_Data.DriveOrderSet	= RXBuff[10] <<8; 		        // 高位数据
//							Job_Data.DriveOrderSet	|= RXBuff[11];                // 低位数据
//						}
//						break;
					  case 9:
						if(RXBuff[4] == RXBuff[5])//2位校验
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
								  case 6:
									   Job_Data.AUTOMaterialMode = RXBuff[2];
									break;
								  case 7:
									   Job_Data.AUTOMaterialThickness = RXBuff[2];
									break;
								  case 8:
									   Job_Data.WeldAUTOKeySetMode = RXBuff[2];
									break;
								  case 9:
									   Job_Data.AUTOSetCurrent = RXBuff[2];
									break;
								  case 10:
									break;
								  case 11:
									break;
								  case 12:
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.AUTOMaterialMode = RXBuff[6];              // 数据1 高位
							Job_Data.AUTOMaterialThickness = RXBuff[7];	              // 数据2 低位	
							Job_Data.WeldAUTOKeySetMode = RXBuff[8]; 		            // 高位数据
							Job_Data.AUTOSetCurrent = RXBuff[9];                     // 低位数据
//							if(REM_GUN_EN == ENABLE)
//              {
//							    Job_Data.FgWeldRunEn = RXBuff[13];                     // 低位数据
//							}
							Msg_Key.EParam = TRUE;	 
							
//							Job_Data.Fg_TX_USART1_Finish = FALSE;
//							Job_Data.Fg_TX_USART1_Count = 0;			 
//						  Job_Data.TX_USART1_Array = 9;
							
						}
						break;
					  case 10:
						if((RXBuff[4] == RXBuff[5])&&(Job_Data.FgCURRENTIndicateLedEn == FALSE))//2位校验后没有焊接的情况下解码数据
						{
							  Job_Data.FgEepromSave_EXECUTE = RXBuff[1]&0x01;
							  Job_Data.FgEepromProcess_EXECUTE = (RXBuff[1]<<1)&0x01;
							  Job_Data.FgEepromProcessEn = RXBuff[2];
							  Job_Data.FgEepromSaveEn = RXBuff[3];
							  Job_Data.WeldWorkSetMode =  RXBuff[6];	                // 数据1 高位
						    Job_Data.WeldRunSetMode = RXBuff[7];
						    Job_Data.WeldPulseSetMode = RXBuff[8];
						    Job_Data.MIGMaterialDia = RXBuff[9];
						    Job_Data.MIGMaterialMode = RXBuff[10];
							  Job_Data.WeldRunSetVRD	= RXBuff[11];                  // 低位数据
							  Job_Data.LanguageMode	= RXBuff[12];                    // 低位数据
								Job_Data.JobWorkSet = RXBuff[13];                      // 低位数据
	              Job_Data.DriveOrderSet   = NO_ORDER_KEY;               // 防止复位时机器发波
							  Msg_Key.EParam = TRUE;	
							  if(Job_Data.FgEepromSave_EXECUTE == ENABLE)
								{
										EEPROM_SaveInJob(Job_Data.JobWorkSet);                     // 存储当前job
										EEPROM_SaveInFlash (Job_Data.JobWorkSet, DEF_ENABLED);     // 存入rom；
				            COMMOND_TimeOutProcessing();                               // 2023.04.21 增加				
								}
								else if(Job_Data.FgEepromProcess_EXECUTE == ENABLE)
								{
  									EEPROM_LaodInJob(Job_Data.JobWorkSet);
                    COMMOND_TimeOutProcessing();                               // 2023.04.21 增加				
								}
//							  if((Job_Data.FgEepromSave_EXECUTE == ENABLE)&&(Job_Data.FgEepromSaveEn == ENABLE)) 
//								{
//										EEPROM_SaveInJob(Job_Data.JobWorkSet);                     // 存储当前job
//										EEPROM_SaveInFlash (Job_Data.JobWorkSet, DEF_ENABLED);     // 存入rom；									
//								}
//								else if((Job_Data.FgEepromSave_EXECUTE == ENABLE)&&(Job_Data.FgEepromProcessEn == ENABLE)) 
//								{
//				            EEPROM_LaodInJob(Job_Data.JobWorkSet);									
//								}
						}
						break;
					  case 11:                                                  // 云端数据 
						if(RXBuff[4] == RXBuff[5])//2位校验
						{
							switch(RXBuff[1])                                       // 再次接收一次调节值
							{
//								  case 6:
//									   Job_Data.AUTOMaterialMode = RXBuff[2];
//									break;
//								  case 7:
//									   Job_Data.AUTOMaterialThickness = RXBuff[2];
//									break;
//								  case 8:
//									   Job_Data.WeldAUTOKeySetMode = RXBuff[2];
//									break;
//								  case 9:
//									   Job_Data.AUTOSetCurrent = RXBuff[2];
//									break;
								  case 10:
									break;
								  case 11:
									break;
								  case 12:
									break;
								  case 13:
									break;
							    default	:
						      break;												
							}
							Job_Data.AUTOMaterialMode = RXBuff[6];              // 材料种类
							Job_Data.AUTOMaterialThickness = RXBuff[7];	  // 焊接板厚  高位	
							Job_Data.MIGPanelSetMotorSpeed = RXBuff[8] >> 8;	  // 送丝速度  高位
							Job_Data.MIGPanelSetMotorSpeed = RXBuff[9];	      // 送丝速度  低位
							Job_Data.MIGMaterialDia = RXBuff[10];	              // 焊丝直径
							Job_Data.WorldClockHour = RXBuff[11];
							Job_Data.WorldClockMinute = RXBuff[12];
							Job_Data.WorldClockSecond = RXBuff[13];
							Msg_Key.EParam = TRUE;	
							
							Job_Data.Fg_TX_USART1_Finish = FALSE;
							Job_Data.Fg_TX_USART1_Count = 0;			 
						  Job_Data.TX_USART1_Array = 9;
							
						}
						break;
						
						default	:
						break;					
					
				}
//			  Job_Data.Fg_RX_USART1_Finish = FALSE;   /* 数据读取完成   */
        UsartCnnt = 0;
//				Msg_Key.WParam = TRUE;                  // 读取数据后设置按键标志位  22.7.7				
		} 
//		else 
//		{
//				UsartCnnt++;
//				if (UsartCnnt > 1) 
//				{
//						UsartCnnt = 0;
//						for (i = 0; i < 16; i++) 
//						{
//								RXBuff[i] = 0;
//						}
////						Job_Data.Fg_UsartConnect = DISABLE;
//			  Job_Data.Fg_RX_USART1_Finish = FALSE;   /* 数据读取完成   */
//				}		
//		}
}
/*
*********************************************************************************************************
*                                     UART_SendData
*
* Description : UART Send Data.
*
* Arguments   : 1ms调用.
*
* Returns     : None.
*********************************************************************************************************
*/

void USART_SendCode(void)                                                // 发送数据
{
	static uint8 i,j;
//	static uint8 TXBuff[16];     
	
		if(Job_Data.Fg_TX_USART1_Count<50)
		{   
				switch(Job_Data.TX_USART1_Array)
				{
			 case 1:                                                    // 按键及显示指令参数设置()
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0001;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0001;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.KeyMenuSetMode;                    // 低位数据
					TXBuff[7] =  Job_Data.WeldMIGKeySetMode;	              // 数据2 低位	
					TXBuff[8]	= Job_Data.WeldTIGKeySetMode; 		            // 高位数据
					TXBuff[9]	= Job_Data.WeldMMAKeySetMode;                 // 低位数据
					TXBuff[10]	= Job_Data.WeldAUTOKeySetMode; 		          // 高位数据
					TXBuff[11]	= Job_Data.WeldMIGSubKeySetMode;            // 低位数据
					TXBuff[12]	= Job_Data.FgWaterWorkEn; 		              // 高位数据
					TXBuff[13]	= Job_Data.MIGSinglePluseDuty;              // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;	
			 case 2:                                                    // 参数设置(速度 电压 电感 电压微调)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0002;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0002;                                     // 显示电流(变量) 地址
					TXBuff[6] = Job_Data.MIGSetMotorSpeed >>8;              // 数据1 高位
					TXBuff[7] =  Job_Data.MIGSetMotorSpeed;	                // 数据2 低位	
					TXBuff[8]	= Job_Data.MIGSetVoltage >>8; 		            // 高位数据
					TXBuff[9]	= Job_Data.MIGSetVoltage;                     // 低位数据
					TXBuff[10]	= Job_Data.MIGSetInductance >>8; 		        // 高位数据
					TXBuff[11]	= Job_Data.MIGSetInductance;                // 低位数据
					TXBuff[12]	= Job_Data.MIGSetVoltageFine>>8; 		        // 高位数据
					TXBuff[13]	= Job_Data.MIGSetVoltageFine;               // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;	
			 case 3:                                                    // 单脉冲参数及板厚(单脉冲频率,单脉冲占空比)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0003;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0003;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.MIGSetSinglePluseFrequencyFine >>8; 		  // 高位数据
					TXBuff[7]	= Job_Data.MIGSetSinglePluseFrequencyFine;           // 低位数据
					TXBuff[8]	= Job_Data.MIGSetSinglePluseDutyFine >>8; 		        // 高位数据
					TXBuff[9]	= Job_Data.MIGSetSinglePluseDutyFine;                // 低位数据
					TXBuff[10]	= Job_Data.MIGMaterialThickness >>8; 		    // 高位数据
					TXBuff[11]	= Job_Data.MIGMaterialThickness;            // 低位数据
//					TXBuff[12]	= Job_Data.MIGSinglePluseFrequency>>8; 		        // 高位数据
//					TXBuff[13]	= Job_Data.MIGSinglePluseFrequency;               // 低位数据
					TXBuff[12]	= Job_Data.FgRemControlEn;                  // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;	
			 case 4:                                                    // 双脉冲参数设置(峰值速度,基值速度,双脉冲频率,双脉冲占空比)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0004;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0004;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.MIGSetDoublePlusePeakSpeed >>8; 		// 高位数据
					TXBuff[7]	= Job_Data.MIGSetDoublePlusePeakSpeed;        // 低位数据
					TXBuff[8]	= Job_Data.MIGSetDoublePluseBaseSpeedRatio >>8; 		// 高位数据
					TXBuff[9]	= Job_Data.MIGSetDoublePluseBaseSpeedRatio;        // 低位数据
					TXBuff[10]	= Job_Data.MIGSetDoublePluseFrequency >>8; 	// 高位数据
					TXBuff[11]	= Job_Data.MIGSetDoublePluseFrequency;      // 低位数据
					TXBuff[12]	= Job_Data.MIGSetDoublePluseDuty >>8; 		  // 高位数据
					TXBuff[13]	= Job_Data.MIGSetDoublePluseDuty;           // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;	
			 case 5:                                                    // MIG其他参数(点焊时间,间隙时间,前气时间,后气时间)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0005;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0005;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.MIGSetPreTime>>8; 		              // 高位数据
					TXBuff[7]	= Job_Data.MIGSetPreTime;                     // 低位数据
					TXBuff[8]	= Job_Data.MIGSetPostTime>>8; 		            // 高位数据
					TXBuff[9]	= Job_Data.MIGSetPostTime;                    // 低位数据
					TXBuff[10]	= Job_Data.MIGSetSpotTime>>8; 		            // 高位数据
					TXBuff[11]	= Job_Data.MIGSetSpotTime;                    // 低位数据
					TXBuff[12]	= Job_Data.MIGSetStopTime>>8; 		            // 高位数据
					TXBuff[13]	= Job_Data.MIGSetStopTime;                    // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;	
			 case 6:                                                    // MIG模式4T设置参数
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0006;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0006;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.MIGSetStartMotorSpeed>>8; 		      // 高位数据
					TXBuff[7]	= Job_Data.MIGSetStartMotorSpeed;             // 低位数据
					TXBuff[8]	= Job_Data.MIGSetUpSlopeTime>>8; 		          // 高位数据
					TXBuff[9]	= Job_Data.MIGSetUpSlopeTime;                 // 低位数据
					TXBuff[10]	= Job_Data.MIGSetDownSlopeTime>>8; 		        // 高位数据
					TXBuff[11]	= Job_Data.MIGSetDownSlopeTime;               // 低位数据
					TXBuff[12]	= Job_Data.MIGSetCraterMotorSpeed>>8; 		    // 高位数据
					TXBuff[13]	= Job_Data.MIGSetCraterMotorSpeed;            // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;						 
				case 7:                                                   // 手焊氩焊设置参数(电流,热引弧,推力)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[4]	= 0x0007;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x0007;                                     // 显示电流(变量) 地址
					TXBuff[6]	= Job_Data.MMASetCurrent >>8; 		            // 高位数据
					TXBuff[7]	= Job_Data.MMASetCurrent;                     // 低位数据
					if((Model_Num	== 354)||(Model_Num	== 504))
					{
							TXBuff[8]	= Job_Data.MMASetHotCurrent >>8; 		          // 高位数据
							TXBuff[9]	= Job_Data.MMASetHotCurrent;                  // 低位数据
							TXBuff[10]	= Job_Data.MMASetForceCurrent >>8; 		      // 高位数据
							TXBuff[11]	= Job_Data.MMASetForceCurrent;              // 低位数据
					}
					else
					{
							TXBuff[8]	= Job_Data.MMASetHotCurrent >>8; 		          // 高位数据
							TXBuff[9]	= Job_Data.MMASetHotCurrent;                  // 低位数据
							TXBuff[10]	= Job_Data.MMASetForceCurrent >>8; 		      // 高位数据
							TXBuff[11]	= Job_Data.MMASetForceCurrent;              // 低位数据
					}					 												
					TXBuff[12]	= Job_Data.TIGSetPeakCurrent >>8; 		          // 高位数据
					TXBuff[13]	= Job_Data.TIGSetPeakCurrent;                   // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
					break;
					case 8:                                                   // 手焊氩焊设置参数(电流,热引弧,推力)
					TXBuff[0]	= 0x00A5;                                     // 帧头 165
					TXBuff[1]	= Job_Data.LcmCurrentData>>8; 		            // 高位数据
					TXBuff[2]	= Job_Data.LcmCurrentData;                    // 低位数据
					TXBuff[3]	= Job_Data.DriveOrderSet;                     // 低位数据		
					TXBuff[4]	= 0x0008;                                     // 指令数 每次发送10个8位数据; 6-13,14保留,最后一位为复位时间
					TXBuff[5]	= 0x0008;                                     // 指令类型-下发指令				 
					TXBuff[6]	= Job_Data.LcmCurrentData>>8; 		            // 高位数据
					TXBuff[7]	= Job_Data.LcmCurrentData;                    // 低位数据
					TXBuff[8]	= Job_Data.LcmVoltageData>>8; 		            // 高位数据
					TXBuff[9]	= Job_Data.LcmVoltageData;                    // 低位数据
					TXBuff[10]	= Job_Data.SystemWorkTime>>24; 		            // 高位数据
					TXBuff[11]	= Job_Data.SystemWorkTime>>16;                // 低位数据
					TXBuff[12]	= Job_Data.SystemWorkTime>>8; 		            // 高位数据
					TXBuff[13]	= Job_Data.SystemWorkTime;                    // 低位数据
					TXBuff[14]	= Job_Data.LcmVoltageData>>8; 		            // 高位数据
					TXBuff[15]	= Job_Data.LcmVoltageData;                    // 低位数据
						break;
					case 9:                                                   // 手焊氩焊设置参数(电流,热引弧,推力)
					TXBuff[0]	= 0x00A5;                                     // 帧头
					TXBuff[1]	= Job_Data.TX_USART1_Value;                                     // 帧头					 						 
					TXBuff[2]	= 0x000A;                                     // 指令数 每次发送10个8位数据; 6-13,14保留,最后一位为复位时间
					TXBuff[3]	= 0x0082;                                     // 指令类型-下发指令				 
					TXBuff[4]	= 0x0009;                                     // 指令数 每次发送10个8位数据; 6-13,14保留,最后一位为复位时间
					TXBuff[5]	= 0x0009;                                     // 指令类型-下发指令				 
					TXBuff[6]	= Job_Data.AUTOMaterialMode; 		            // 高位数据
					TXBuff[7]	= Job_Data.AUTOMaterialThickness;                    // 低位数据
					TXBuff[8]	= Job_Data.WeldAUTOKeySetMode; 		            // 高位数据
					TXBuff[9]	= Job_Data.AUTOSetCurrent;                    // 低位数据
					TXBuff[10]	= Job_Data.PowerVoltage>>8; 		                // 输入电压
					TXBuff[11]	= Job_Data.PowerVoltage;                    // 输入电压
					TXBuff[12]	= Job_Data.LcmOrderSet; 		                // 高位数据
					TXBuff[13]	= Msg_Key.errIParam;                        // 低位数据
					TXBuff[1]	= Job_Data.TX_USART1_Value;                   // 具体参数值				 						 
					TXBuff[2]	= TXBuff[Job_Data.TX_USART1_Value];           // 重复发送一次当前值
					TXBuff[3]	= TXBuff[(Job_Data.TX_USART1_Value+1)];       // 重复发送一次当前值		 
						break;
				 case 10:                                                 // 功能设置
					TXBuff[0]	= 0x00A5;                                     // 帧头
				  TXBuff[1] = Job_Data.FgEepromSave_EXECUTE;
				  TXBuff[1] |= (Job_Data.FgEepromProcess_EXECUTE << 1);
					TXBuff[2]	= Job_Data.FgEepromProcessEn;                    // 低位数据
					TXBuff[3]	= Job_Data.FgEepromSaveEn;                      // 低位数据
					TXBuff[4]	= 0x000A;                                     // 显示电流(变量) 地址
					TXBuff[5]	= 0x000A;                                     // 显示电流(变量) 地址
					TXBuff[6] =  Job_Data.WeldWorkSetMode;	                // 数据1 高位
					TXBuff[7] =  Job_Data.WeldRunSetMode;                   // 数据2 低位	 
					TXBuff[8] =  Job_Data.WeldPulseSetMode;	                // 数据2 低位	
					TXBuff[9] =  Job_Data.MIGMaterialDia;	                  // 数据2 低位	
					TXBuff[10] =  Job_Data.MIGMaterialMode;	                // 数据2 低位	
					TXBuff[11]	= Job_Data.WeldRunSetVRD;                   // 低位数据
					TXBuff[12]	= Job_Data.LanguageMode;                    // 低位数据
					TXBuff[13]	= Job_Data.JobWorkSet;                      // 低位数据
					break;
				default	:
				break;					
			 }
				j=Job_Data.Fg_TX_USART1_Count%10;				
				Job_Data.Fg_TX_USART1_Count++; 
			  Job_Data.Fg_RX_USART1_Finish = FALSE;
		}
    else
    {
				Job_Data.Fg_TX_USART1_Count = 0;
				Job_Data.Fg_TX_USART1_Finish = TRUE;
		}	
		if((Job_Data.FgCURRENTIndicateLedEn == TRUE)||(Job_Data.FgLcmHoldEn == ENABLE))
		{
				Job_Data.Fg_TX_USART1_Count = 49;
				Job_Data.Fg_TX_USART1_Finish = FALSE;	
        Job_Data.TX_USART1_Array = 8;	
        Job_Data.TX_USART1_Value = 6;				
		}
    else
    {
				TXBuff[14]	= 0xFF; 		                   // 高位数据
				TXBuff[15]	= 0xFF;                        // 低位数据
		}			
//		Send_ValueDisplay();
}

void USART_SendCode_AI(void)                                      // 云端发送数据
{
	static uint8 i,j;
	
		if(1)
		{   
				switch(1)
				{
			    case 1:                                                    // 
					TXBuff_AI[0]	= 0x00A5;                                     // 预留-帧头-标志位
					TXBuff_AI[1]	= Job_Data.TX_USART1_Value;                   // 预留-参数类别				 						 
					TXBuff_AI[2]	= Job_Data.TX_USART1_Address >>8;           // 预留-参数地址高位
					TXBuff_AI[3]	= Job_Data.TX_USART1_Address;       // 预留-参数地址低位 
					TXBuff_AI[4]	= Job_Data.TX_USART1_Long >>8;                                     // 预留-参数长度高位
					TXBuff_AI[5]	= Job_Data.TX_USART1_Long;                                     // 预留-参数长度低位
					TXBuff_AI[6]  = Job_Data.WeldWorkSetMode;	                // weld mode			 
					TXBuff_AI[7]	= Job_Data.WeldRunSetMode;                    // 2T/4T
					TXBuff_AI[8]  = Job_Data.WeldPulseSetMode;	              // Pulse Mode
					TXBuff_AI[9]	= Job_Data.MIGMaterialDia; 		            // Wire diameter
					TXBuff_AI[10]	= Job_Data.MIGMaterialMode;                 // Material selection
					TXBuff_AI[11]	= Job_Data.MIGSetMotorSpeed >>8;		          // feeding speed 
					TXBuff_AI[12]	= Job_Data.MIGSetMotorSpeed;            // feeding speed 
					TXBuff_AI[13]	= Job_Data.MIGSetVoltage >> 8; 		              // welding set voltage
					TXBuff_AI[14]	= Job_Data.MIGSetVoltage;              // welding set voltage
					TXBuff_AI[15] = Job_Data.MIGSetInductance >>8;              // inductance
					TXBuff_AI[16] = Job_Data.MIGSetInductance ;              // inductance
					TXBuff_AI[17] = Job_Data.MIGSetSinglePluseFrequencyFine >>8;	  // pulse frequency   0-60  对应  -30%-30%
					TXBuff_AI[18]	= Job_Data.MIGSetSinglePluseFrequencyFine;// pulse frequency
					TXBuff_AI[19]	= Job_Data.MIGSetSinglePluseDutyFine >>8;     // pulse duty       0-60  对应  -30%-30%
					TXBuff_AI[20]	= Job_Data.MIGSetSinglePluseDutyFine; 		        // pulse duty
					TXBuff_AI[21]	= Job_Data.MMASetCurrent >>8; 		            // MMA current
					TXBuff_AI[22]	= Job_Data.MMASetCurrent;                     // MMA current
					TXBuff_AI[23]	= Job_Data.MMASetHotCurrent >>8; 		          // Hot start current
					TXBuff_AI[24]	= Job_Data.MMASetHotCurrent;                  // Hot start current
					TXBuff_AI[25]	= Job_Data.MMASetForceCurrent >>8; 		      // force current
					TXBuff_AI[26]	= Job_Data.MMASetForceCurrent;              // force current
					TXBuff_AI[27]	= Job_Data.TIGSetPeakCurrent >>8;                // TIG current
					TXBuff_AI[28]	= Job_Data.TIGSetPeakCurrent; 		    // TIG current
					TXBuff_AI[29]	= Job_Data.WeldRunSetVRD;                // VRD
					TXBuff_AI[30]	= Job_Data.FgRemControlEn;                  // REM 远控标志
					
					TXBuff_AI[31]	= Job_Data.MIGSetDoublePlusePeakSpeed >>8; 		// MIG 双脉冲峰值电流
					TXBuff_AI[32]	= Job_Data.MIGSetDoublePlusePeakSpeed;        // MIG 双脉冲峰值电流
					TXBuff_AI[33]	= Job_Data.MIGSetDoublePluseBaseSpeedRatio >>8;// MIG 双脉冲基值电流
					TXBuff_AI[34]	= Job_Data.MIGSetDoublePluseBaseSpeedRatio;        // MIG 双脉冲基值电流
					TXBuff_AI[35]	= Job_Data.MIGSetDoublePluseFrequency >>8; 	// MIG 双脉冲频率
					TXBuff_AI[36]	= Job_Data.MIGSetDoublePluseFrequency;      // MIG 双脉冲频率
					TXBuff_AI[37]	= Job_Data.MIGSetDoublePluseDuty >>8; 		  // MIG 双脉冲占空比
					TXBuff_AI[38]	= Job_Data.MIGSetDoublePluseDuty;           // MIG 双脉冲占空比
					TXBuff_AI[39]	= 0;           // 预留
					TXBuff_AI[40]	= 0;           // 预留
					
					TXBuff_AI[41]	= Job_Data.MIGSetPreTime>>8; 		              // MIG 前气时间
					TXBuff_AI[42]	= Job_Data.MIGSetPreTime;                     // MIG 前气时间
					TXBuff_AI[43]	= Job_Data.MIGSetStartMotorSpeed>>8; 		      // MIG 起弧电流
					TXBuff_AI[44]	= Job_Data.MIGSetStartMotorSpeed;             // MIG 起弧电流
					TXBuff_AI[45]	= Job_Data.MIGSetUpSlopeTime>>8; 		          // MIG 缓升时间
					TXBuff_AI[46]	= Job_Data.MIGSetUpSlopeTime;                 // MIG 缓升时间
					TXBuff_AI[47]	= Job_Data.MIGSetDownSlopeTime>>8; 		        // MIG 缓降时间
					TXBuff_AI[48]	= Job_Data.MIGSetDownSlopeTime;               // MIG 缓降时间
					TXBuff_AI[49]	= Job_Data.MIGSetCraterMotorSpeed>>8; 		    // MIG 收弧电流
					TXBuff_AI[50]	= Job_Data.MIGSetCraterMotorSpeed;            // MIG 收弧电流
					TXBuff_AI[51]	= Job_Data.MIGSetPostTime>>8; 		            // MIG 后气时间
					TXBuff_AI[52]	= Job_Data.MIGSetPostTime;                    // MIG 后气时间
					TXBuff_AI[53]	= Job_Data.MIGSetSpotTime>>8; 		            // MIG 点焊时间
					TXBuff_AI[54]	= Job_Data.MIGSetSpotTime;                    // MIG 点焊时间
					TXBuff_AI[55]	= Job_Data.MIGSetStopTime>>8; 		            // MIG 停止时间
					TXBuff_AI[56]	= Job_Data.MIGSetStopTime;                    // MIG 停止时间
					TXBuff_AI[57]	= Job_Data.MIGAutoSetMotorSpeed>>8; 		      // AUTO 送丝速度
					TXBuff_AI[58]	= Job_Data.MIGAutoSetMotorSpeed; 		          // AUTO 送丝速度
					TXBuff_AI[59]	= Job_Data.MIGMaterialThickness>>8; 		      // MIG 模式焊接板厚
					TXBuff_AI[60]	= Job_Data.MIGMaterialThickness;              // MIG 模式焊接板厚
					
					TXBuff_AI[61]	= Job_Data.MIGSetCurrent >> 8; 		           // welding set current  根据速度计算出来
					TXBuff_AI[62]	= Job_Data.MIGSetCurrent;                    // welding set current  根据速度计算出来
					TXBuff_AI[71]	= Job_Data.MIGSetVoltageFine>>8; 		         // 焊接电压微调
					TXBuff_AI[72]	= Job_Data.MIGSetVoltageFine;                // 焊接电压微调
					TXBuff_AI[63]	= Job_Data.LcmCurrentData>>8; 		            // 焊接显示电流
					TXBuff_AI[64]	= Job_Data.LcmCurrentData;                    // 焊接显示电流
					TXBuff_AI[65]	= Job_Data.LcmVoltageData>>8; 		            // 焊接显示电压
					TXBuff_AI[66]	= Job_Data.LcmVoltageData;                    // 焊接显示电压
					TXBuff_AI[67]	= Job_Data.SystemWorkTime>>24; 		            // 焊接工作时长
					TXBuff_AI[68]	= Job_Data.SystemWorkTime>>16;                // 焊接工作时长
					TXBuff_AI[69]	= Job_Data.SystemWorkTime>>8; 		            // 焊接工作时长
					TXBuff_AI[70]	= Job_Data.SystemWorkTime;                    // 焊接工作时长
					TXBuff_AI[73]	= Job_Data.AUTOMaterialMode; 		              // 自动模式材料选择
					TXBuff_AI[74]	= Job_Data.AUTOMaterialThickness >> 8;        // 自动模式焊接板厚
					TXBuff_AI[75]	= Job_Data.AUTOMaterialThickness; 		        // 自动模式焊接板厚
					TXBuff_AI[76]	= Job_Data.AUTOSetCurrent >> 8;               // 自动模式焊接电流微调 0-100 显示-50% 到 50%
					TXBuff_AI[76]	= Job_Data.AUTOSetCurrent;                    // 自动模式焊接电流微调 0-100 显示-50% 到 50%
					TXBuff_AI[77]	= Job_Data.PowerVoltage>>8; 		              // 输入电压
					TXBuff_AI[78]	= Job_Data.PowerVoltage;                      // 输入电压
					
					TXBuff_AI[81]	= Job_Data.LcmOrderSet; 		                // 显示指令
					TXBuff_AI[82]	= Job_Data.DriveOrderSet;                     // 驱动指令		
					TXBuff_AI[83]	= Msg_Key.errIParam;                        // 报错信息
				  TXBuff_AI[84] = Job_Data.FgEepromSave_EXECUTE;              // 保存指令
				  TXBuff_AI[85] = Job_Data.FgEepromProcess_EXECUTE;           // 调用指令
					TXBuff_AI[86]	= Job_Data.FgEepromProcessEn;                    // 保存使能
					TXBuff_AI[87]	= Job_Data.FgEepromSaveEn;                      // 调用使能
					TXBuff_AI[88]	= Job_Data.LanguageMode;                    // 语言设置
					TXBuff_AI[89]	= Job_Data.JobWorkSet;                      // 数据库设置
					
					TXBuff_AI[90]	= Job_Data.KeyMenuSetMode;                    // 按键菜单层次
					TXBuff_AI[91] =  Job_Data.WeldMIGKeySetMode;	              // MIG功能按键功能页面
					TXBuff_AI[92]	= Job_Data.WeldTIGKeySetMode; 		            // TIG功能按键功能页面
					TXBuff_AI[93]	= Job_Data.WeldMMAKeySetMode;                 // MMA功能按键功能页面
					TXBuff_AI[94]	= Job_Data.WeldAUTOKeySetMode; 		          // 自动模式功能按键功能页面
					TXBuff_AI[95]	= Job_Data.WeldMIGSubKeySetMode;            // MIG功能按键子菜单
					TXBuff_AI[96]	= Job_Data.FgWaterWorkEn; 		              // 水冷开关标志
					TXBuff_AI[97]	= Job_Data.MIGSinglePluseDuty;              // 单脉冲占空比
					TXBuff_AI[98]	= Job_Data.MIGSinglePluseFrequency;         // 单脉冲占空比
					
					break;
				default	:
				break;					 
			 }
		}
}

void USART1_IRQHandler(void)
{
		static uint16 DataBuff, temp;
		static uint16 Num, FgStar = 0;
		static uint8  i = 0;
		
		if (USART_GetFlagStatus(USART1, USART_FLAG_ORE) != RESET)    //  
		{		
				USART_ClearFlag(USART1, USART_FLAG_ORE);	
				temp = USART_ReceiveData(USART1);		
		}		
		if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)            
		{
				USART_ClearITPendingBit(USART1, USART_IT_RXNE);
				DataBuff = USART_ReceiveData(USART1);
			//--------------------
					if(USART_RX_CNT < 64)
		{
			USART2_RX_BUF[USART_RX_CNT] = DataBuff;			//记录接收到的值
			USART_RX_CNT ++;								//接收数据增加1 
		} 
		//--------------------
//				Num =  DataBuff;
//				if ((Num == 0xA5) && (FgStar == 0)) 
//				{  
//					 FgStar = 1;
//				}
//				if (FgStar == 1)
//				{
//						RXBuff[i] = DataBuff;
//						i++;
//						if (i > 15) 
//						{
//								i = 0;
//								FgStar = 0;
//								Job_Data.Fg_RX_USART1_Finish = TRUE;
////								USART_DecodeData();
//						}		
//				}
		}		
}
uint8 CountUsartTest; 

void Send_ValueDisplay(void)
{ 	 
	   static uint8 Count,TimeCount; 
		 GPIO_ResetBits(GPIOD,GPIOD_WorkDisplay_EN);                    // 打开485,设置为输出模式;
		 GPIO_ResetBits(GPIOA,GPIOA_USART_EN);                          // 打开485,设置为输出模式;
//	   TXBuff[15] = 0x12;
	   for(Count=0;Count<16;)
	   {
		     Job_Data.Fg_TX1Finish = USART_GetFlagStatus(USART1, USART_FLAG_TC);
			   if (Job_Data.Fg_TX1Finish == ENABLE)
				 {			 
					   CountUsartTest = Count;
						 USART_SendData(USART1, TXBuff[Count]);
             Count++;		
				 }
				 TimeCount = 0;
		 }		 
	   GPIO_SetBits(GPIOD,GPIOD_WorkDisplay_EN);                      // 关闭485,设置为输入模式
		 GPIO_SetBits(GPIOA,GPIOA_USART_EN);                            // 关闭485,设置为输入模式
}

/*
*********************************************************************************************************
*********************************************************************************************************
**                                         END
*********************************************************************************************************
*********************************************************************************************************
*/

/****************************************************************************************************
 * 函数名称： void Send_Data(u8 *buf,u8 len)
 * 入口参数：u8 *buf u8 len
 * 返回  值：无
 * 功能说明：串口发送数据
 * 			 buf:发送区首地址
 *			 len:发送的字节数(为了和本代码的接收匹配,这里建议不要超过64个字节)
 ***************************************************************************************************/
void Send_Data(u8 *buf,u8 len)
{
	u8 t;
//	RS485_TX_EN=1;			//设置为发送模式
		 GPIO_ResetBits(GPIOD,GPIOD_WorkDisplay_EN);                    // 打开485,设置为输出模式;
		 GPIO_ResetBits(GPIOA,GPIOA_USART_EN);                          // 打开485,设置为输出模式;
//	delay_ms(1);
	for(t=0;t<len;t++)		//循环发送数据
	{		   
		while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);	  
		USART_SendData(USART1,buf[t]);
	}	 
//	delay_ms(1);

	USART_RX_CNT=0;	  
//	RS485_TX_EN=0;				//设置为接收模式	
	   GPIO_SetBits(GPIOD,GPIOD_WorkDisplay_EN);                      // 关闭485,设置为输入模式
		 GPIO_SetBits(GPIOA,GPIOA_USART_EN);                            // 关闭485,设置为输入模式
}
//------------------
//--------------------
void RS485_byte(u8 d)  //485发送一个字节
{
		 GPIO_ResetBits(GPIOD,GPIOD_WorkDisplay_EN);                    // 打开485,设置为输出模式;
		 GPIO_ResetBits(GPIOA,GPIOA_USART_EN);  
//d=~d;
  USART_SendData(USART1, d);
	  while(USART_GetFlagStatus(USART1,USART_FLAG_TC)==RESET);
  USART_ClearFlag(USART1,USART_FLAG_TC );

	   GPIO_SetBits(GPIOD,GPIOD_WorkDisplay_EN);                      // 关闭485,设置为输入模式
		 GPIO_SetBits(GPIOA,GPIOA_USART_EN); 
  
}
/****************************************************************************************************
 * 函数名称：u8 UartRead(u8 *buf, u8 len) 
 * 入口参数：u8 *buf u8 len
 * 返回  值：u8
 * 功能说明：计算接收的数据长度，并且将数据放到*buf数组中
 ***************************************************************************************************/             
u8 UartRead(u8 *buf, u8 len)  
{
	u8 i;
	if(len > USART_RX_CNT)  		//指定读取长度大于实际接收到的数据长度时
	{
		len = USART_RX_CNT; 		//读取长度设置为实际接收到的数据长度
	}
	
	for(i = 0;i < len;i ++)  		//拷贝接收到的数据到接收指针中
	{
		*buf = USART2_RX_BUF[i];  	//将数据复制到buf中
		buf  ++;
	}
	USART_RX_CNT=0;              	//接收计数器清零
	return len;                   	//返回实际读取长度
}
/****************************************************************************************************
 * 函数名称：void UartRxMonitor(u8 ms)
 * 入口参数：u8 ms
 * 返回  值：无
 * 功能说明：在定时器中调用，用于监控数据接收
 ***************************************************************************************************/   
 	 u8 idletmr      = 0;        		//定义监控时间
void UartRxMonitor(u8 ms) 					
{
	static u8 USART_RX_BKP = 0;  			//定义USART2_RC_BKP暂时存储诗句长度与实际长度比较
//	static u8 idletmr      = 0;        		//定义监控时间
	
	if(USART_RX_CNT > 0)					//接收计数器大于零时，监控总线空闲时间
	{
		if(USART_RX_BKP != USART_RX_CNT) 	//接收计数器改变，即刚接收到数据时，清零空闲计时
		{
			USART_RX_BKP = USART_RX_CNT;  	//赋值操作，将实际长度给USART2_RX_BKP
			idletmr      = 0;               //将监控时间清零
		}
		else                              	//接收计数器未改变，即总线空闲时，累计空闲时间
		{
											              //如果在一帧数据完成之前有超过3.5个字节时间的停顿，接收设备将刷新当前的消息并假定下一个字节是一个新的数据帧的开始
			if(idletmr < 2)                 //空闲时间小于3ms时，持续累加
			{
				idletmr += ms;
				if(idletmr >= 2)            //空闲时间达到3ms时，即判定为1帧接收完毕
				{
					From_Flag = 1;			     //设置命令到达标志，帧接收完毕标志
				}
			}
		}
	}
	else
	{
		USART_RX_BKP = 0;
	}
}

/****************************************************************************************************
 * 函数名称：void UartRxMonitor(u8 ms)
 * 入口参数：u8 ms
 * 返回  值：无
 * 功能说明：串口驱动函数，检测数据帧的接收，调度功能函数，需在主循环中调用
 *           这里是主机，所以在功能调度函数里只需要得到读命令返回的数据，
 *           得到的数据根据自已的需要使用即可，这里是基于modbus协议，所以
 *           需要对照modbus协议去理解，请查阅资料里的modbus资料
 ***************************************************************************************************/   
unsigned char buf[64];
	unsigned char crch,crcl;
void UartDriver(void)
{
	unsigned int i;	
	unsigned int crc;
//	unsigned char crch,crcl;
	static unsigned char len;
//	static unsigned char buf[64];
//	USART_DecodeData();
	if (From_Flag)            									//帧接收完成标志，即接收到一帧新数据
	{
		From_Flag = 0;           								//帧接收完成标志清零
		len       = UartRead(buf,sizeof(buf));   				//将接收到的命令读到缓冲区中
		crc       = GetCRC16(buf,len-2);       					//计算CRC校验值，除去CRC校验值
		crch=crc  >> 8;    										//crc高位
		crcl=crc  &  0xFF;										//crc低位

		if((buf[len-2] == crch) && (buf[len-1] == crcl))  		//判断CRC校验是否正确
		{
			if (buf[1] == 0x03)									//0x03 读命令
			{
//				if((buf[2] == 0x00) && (buf[3] <= 0x05))  		//寄存器地址支持0x0000~0x0005
				{
					/* 通过上面的验证判断后 在这里可直接获取数据 保存在ReadDateVal中 */
//					Job_Data.MIGPanelSetMotorSpeed  = buf[5] * 256 + buf[6];
					for(i=0;i<len;i++)
					  {
					     RXBuff[i] = buf[i+3];
						}
						USART_DecodeData();
				}
			}
			/* 写命令不需要数据只需要应答即可 */
			if (buf[1] == 0x06)									 //0x06 写命令
			{
					Job_Data.Fg_TX_USART1_Finish = TRUE;
				  Job_Data.Fg_TX_Finish_Count = 0;
			}
			/* 判断校验码正确后 无论是读还是写 都清零485忙标志，表示收到应答，释放485，可进行其它命令操作 */
			RS485Busy = 0;										
		}
	}
}

/****************************************************************************************************
 * 函数名称：void RS485_RW_Opr(u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate)
 * 入口参数：u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate
 * 			 ucAddr：从机地址
 *			 ucCmd ：功能码 03->读	06->写
 *			 ucReg ：寄存器地址
 *			 uiDate：写操作即是发送的数据 读操作即是读取数据个数
 * 返回  值：无
 * 功能说明：485读写操作函数
 ***************************************************************************************************/   
unsigned char ucBuf[128];
unsigned char kkk;
void RS485_RW_Opr(u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate)
{
	unsigned int crc;
	unsigned char crcl;
	unsigned char crch;	
  USART_SendCode();


	ucBuf[0] = ucAddr;				/* 从机地址 */
	ucBuf[1] = ucCmd;				  /* 命令 06 写 03 读 */
	ucBuf[2] = ucReg >> 8;		/* 寄存器地址高位 */
	ucBuf[3] = ucReg;				  /* 寄存器地址低位 */
	
	ucBuf[4] = TXBuff[0];     // 帧头
	ucBuf[5] = TXBuff[1];     // 数据在数组内标识号
	ucBuf[6] = TXBuff[2];     // 重复数高位	
	ucBuf[7] = TXBuff[3];     // 重复数低位
	ucBuf[8] = TXBuff[4];     // 数据组标识0-10,可扩展
	ucBuf[9] = TXBuff[5];     // 数据组标识0-10,可扩展
	ucBuf[10] = TXBuff[6];    // 数据
	ucBuf[11] = TXBuff[7];    // 数据
	ucBuf[12] = TXBuff[8];    // 数据
	ucBuf[13] = TXBuff[9];    // 数据
	ucBuf[14] = TXBuff[10];   // 数据
	ucBuf[15] = TXBuff[11];   // 数据
	ucBuf[16] = TXBuff[12];   // 数据
	ucBuf[17] = TXBuff[13];	  // 数据
	ucBuf[18] = TXBuff[14];   // 预留
	ucBuf[19] = TXBuff[15];	  // 预留
	
	crc      = GetCRC16(ucBuf,20);   /* 计算CRC校验值 */
	crch     = crc >> 8;    		/* crc高位 */
	crcl     = crc &  0xFF;			/* crc低位 */
	ucBuf[20] = crch;				/* 校验高8位 */
	ucBuf[21] = crcl;				/* 校验低8位 */
	Send_Data(ucBuf,23);				/* 发送数据 */
//	RS485Busy = 1;					/* 发送完成后 忙标志置位 */
	RS485Busy = 0;					/* 发送完成后 忙标志置位 */
 kkk=1;      
}

void RS485_RW_Opr_06(u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate)
{
	unsigned int crc;
	unsigned char crcl;
	unsigned char crch;	
  USART_SendCode();	
	
	ucBuf[0] = ucAddr;				/* 从机地址 */
	ucBuf[1] = ucCmd;				  /* 命令 06 写 03 读 */
	ucBuf[2] = ucReg >> 8;	  /* 寄存器地址高位 */
	ucBuf[3] = ucReg;				  /* 寄存器地址低位 */
	//-----------以下是數據---------
	ucBuf[4] = TXBuff[0];     // 帧头
	
	ucBuf[5] = TXBuff[1];     // 数据在数组内标识号
	ucBuf[6] = TXBuff[2];     // 重复数高位
	ucBuf[7] = TXBuff[3];     // 重复数低位
	ucBuf[8] = TXBuff[4];     // 数据组标识
	ucBuf[9] = TXBuff[5];     // 数据组标识
	ucBuf[10] = TXBuff[6];    // 数据
	ucBuf[11] = TXBuff[7];    // 数据
	ucBuf[12] = TXBuff[8];    // 数据
	ucBuf[13] = TXBuff[9];    // 数据
	ucBuf[14] = TXBuff[10];   // 数据
	ucBuf[15] = TXBuff[11];   // 数据
	ucBuf[16] = TXBuff[12];   // 数据
	ucBuf[17] = TXBuff[13];	  // 数据
	ucBuf[18] = TXBuff[14];   // 预留
	ucBuf[19] = TXBuff[15];	  // 预留
	
	crc      = GetCRC16(ucBuf,20);   /* 计算CRC校验值 */
	crch     = crc >> 8;    		/* crc高位 */
	crcl     = crc &  0xFF;			/* crc低位 */
	ucBuf[20] = crch;				/* 校验高8位 */
	ucBuf[21] = crcl;				/* 校验低8位 */
	Send_Data(ucBuf,23);				/* 发送数据 */
//	RS485Busy = 1;					/* 发送完成后 忙标志置位 */
	RS485Busy = 0;					/* 发送完成后 忙标志置位 */
	
//	Job_Data.Fg_TX_USART1_Finish = TRUE;
}


/****************************************************************************************************
 * 函数名称：void RS485_RW_Opr_06(u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate)
 * 入口参数：u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate
 * 			 ucAddr：从机地址
 *			 ucCmd ：07定义为广播校准数据 128位
 *			 ucReg ：寄存器地址
 *			 uiDate：写操作即是发送的数据 读操作即是读取数据个数
 * 返回  值：无
 * 功能说明：485读写操作函数

 ***************************************************************************************************/   
int crctest;
void RS485_RW_Opr_07(u8 ucAddr,u8 ucCmd,u16 ucReg,u16 uiDate)
{
	unsigned int crc;
	unsigned char crcl,i,j;
	unsigned char crch;	
  USART_SendCode_AI();	
	
	ucBuf[0] = ucAddr;				/* 从机地址 */
	ucBuf[1] = ucCmd;				  /* 命令 06 写 03 读 */
	ucBuf[2] = ucReg >> 8;	  /* 寄存器地址高位 */
	ucBuf[3] = ucReg;				  /* 寄存器地址低位 */
	//-----------以下是數據---------
	for(i=4;i<124;i++)
	{
 	    ucBuf[i] = TXBuff_AI[i-4];     // 帧头			 
	}	
//	for(i=4;i<124;i++)
//	{
// 	    ucBuf[i] = 0x11;     // 帧头			 
//	}	
	crc      = GetCRC16(ucBuf,125);   /* 计算CRC校验值 */
	crctest  = crc;
	crch     = crc >> 8;    		/* crc高位 */
	crcl     = crc &  0xFF;			/* crc低位 */
	ucBuf[125] = crch;				/* 校验高8位 */
	ucBuf[126] = crcl;				/* 校验低8位 */	
	Send_Data(ucBuf,128);				/* 发送数据 */
//	RS485Busy = 1;					/* 发送完成后 忙标志置位 */
	RS485Busy = 0;					/* 发送完成后 忙标志置位 */
	
//	Job_Data.Fg_TX_USART1_Finish = TRUE;
}








