<h2 align="center">
  <img src="../assets/bench2drive.jpg" style="width: 100%; height: auto;">
</h2>
<h2 align="center">
基线模型可视化与定性分析
</h2>

我们提供了 Bench2Drive 基线方法的可视化视频和定性分析。对于 TCP、UniAD 和 VAD，我们选取各模型的最佳版本（TCP-traj、UniAD-Base、VAD-Base），并对以下 10 个场景进行可视化。

**注意：加载全部 GIF 可能需要一些时间，请耐心等待。**

<table>
  <tr>
    <th rowspan="2" style="text-align:center">驾驶技能</th> <th rowspan="2" style="text-align:center">场景名称</th> <th rowspan="2" style="text-align:center">路线 ID</th><th colspan="4" style="text-align:center">是否成功</th>
  </tr>
  <tr>
    <td> AD-MLP </td> <td> TCP-traj </td><td>UniAD-Base</td><td>VAD-Base</td>
  </tr>

  <tr>
    <td rowspan="2" style="text-align:center">汇入</td>
    <td>MergerIntoSlowTraffic</td> 
    <td>2283</td> 
    <td>x</td><td>√</td><td>√</td><td>x</td>
  </tr>
  <tr>
    <td>SignalizedJunctionLeftTurn</td>
    <td>4183</td>
    <td>x</td><td>√</td><td>x</td><td>√</td>
  </tr>
  <tr>
    <td rowspan="2" style="text-align:center">超车</td>
    <td>ParkedObstacle</td> 
    <td>25318</td> 
    <td>x</td><td>x</td><td>x</td><td>√</td>
  </tr>
  <tr>
    <td>HazardAtSideLane</td>
    <td>25439</td>
    <td>x</td><td>x</td><td>√</td><td>√</td>
  </tr>
  <tr>
    <td rowspan="2" style="text-align:center">紧急制动</td>
    <td>ParkingCutIn</td> 
    <td>18305</td> 
    <td>x</td><td>√</td><td>√</td><td>x</td>
  </tr>
  <tr>
    <td>StaticCutIn</td>
    <td>26396</td>
    <td>x</td><td>x</td><td>√</td><td>√</td>
  </tr>
  <tr>
    <td rowspan="2" style="text-align:center">让行</td>
    <td>YieldToEmergencyVehicle</td> 
    <td>3378</td> 
    <td>x</td><td>x</td><td>x</td><td>x</td>
  </tr>
  <tr>
    <td>InvadingTurn</td> 
    <td>2802</td> 
    <td>x</td><td>√</td><td>√</td><td>x</td>
  </tr>
  <tr>
    <td rowspan="2" style="text-align:center">交通标志</td>
    <td>EnterActorFlow</td> 
    <td>3749</td> 
    <td>x</td><td>√</td><td>x</td><td>x</td>
  </tr>
  <tr>
    <td>VanillaNonSignalizedTurnEncounterStopsign</td>
    <td>3905</td>
    <td>x</td><td>√</td><td>x</td><td>x</td>
  </tr>
</table>

**注意：本可视化中“成功”的定义与 Bench2Drive 使用的标准定义不同。** 一条路线可能包含多个动作，例如通过交通信号灯后转弯。本可视化只评估所选片段中的动作是否成功。例如，若车辆遵守信号灯并通过路口，但在后续转弯时发生碰撞，在“遵守交通标志”这一项中仍视为成功。

# 汇入

我们通过三个模型在 `MergeIntoSlowTraffic` 和 `SignalizedJunctionLeftTurn` 场景中的行为，展示其汇入能力。在 `MergeIntoSlowTraffic` 中，自车应驶入匝道离开高速公路；在 `SignalizedJunctionLeftTurn` 中，自车应完成左转。

<table>
  <tr>
    <th>案例 ID</th> <th>模型</th> <th>场景</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;前视相机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;BEV&nbsp;&nbsp;&nbsp;&nbsp;</th><th>是否成功</th><th>定性分析</th>
  </tr>
  <tr>
    <td> 1 </td> <td> TCP-traj </td> <td>MergeInto<br>SlowTraffic</td><td><img src="./gifs/2283_tcp_rgb_front_MergerIntoSlowTraffic_success.gif"></td><td><img src="./gifs/2283_tcp_bev_MergerIntoSlowTraffic_success.gif"></td> <td> √ </td><td>自车谨慎变道并成功驶离高速公路，但速度很低（视频为 2 倍速）。</td>
  </tr>  <tr>
    <td> 2 </td><td>  UniAD-Base </td> <td>MergeInto<br>SlowTraffic</td><td><img src="./gifs/2283_uniad_rgb_front_MergerIntoSlowTraffic_success.gif"></td><td><img src="./gifs/2283_uniad_bev_MergerIntoSlowTraffic_success.gif"></td><td> √ </td><td>自车高速变道并成功驶离高速公路。</td>
  </tr>
  <tr>
    <td> 3 </td><td>  VAD-Base </td> <td>MergeInto<br>SlowTraffic</td><td><img src="./gifs/2283_vad_rgb_front_MergerIntoSlowTraffic_failed.gif"></td><td><img src="./gifs/2283_vad_bev_MergerIntoSlowTraffic_failed.gif"></td><td> x </td><td>自车检测到右前方车辆，但仍因车速过快与其相撞。</td>
  </tr>
  <tr>
    <td> 4 </td><td>  TCP-traj </td> <td>Signalized<br>Junction<br>LeftTurn</td><td><img src="./gifs/4183_tcp_rgb_front_SignalizedJunctionLeftTurn_success.gif"></td><td><img src="./gifs/4183_tcp_bev_SignalizedJunctionLeftTurn_success.gif"></td> <td> √ </td><td>自车预测出合适的轨迹，并在路口成功左转。</td>
  </tr>  <tr>
    <td> 5 </td><td>  UniAD-Base </td> <td>Signalized<br>Junction<br>LeftTurn</td><td><img src="./gifs/4183_uniad_rgb_front_SignalizedJunctionLeftTurn_failed.gif"></td><td><img src="./gifs/4183_uniad_bev_SignalizedJunctionLeftTurn_failed.gif"></td><td> x </td><td>自车未能检测到对向来车并继续前进，最终发生碰撞。</td>
  </tr>
  <tr>
    <td> 6 </td><td>  VAD-Base </td> <td>Signalized<br>Junction<br>LeftTurn</td><td><img src="./gifs/4183_vad_rgb_front_SignalizedJunctionLeftTurn_success.gif"></td><td><img src="./gifs/4183_vad_bev_SignalizedJunctionLeftTurn_success.gif"></td><td> √ </td><td>自车检测并预测附近车辆的运动，平稳完成左转。</td>
  </tr>

</table>

# 超车

我们通过三个模型在 `ParkedObstacle` 和 `HazardAtSideLane` 场景中的行为，展示其超车能力。在 `ParkedObstacle` 中，自车会遇到占据部分车道的停放车辆；在 `HazardAtSideLane` 中，自车会遇到占据部分车道的低速危险目标。自车应通过变道避让。

<table>
  <tr>
    <th>案例 ID</th><th>模型</th> <th>场景</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;前视相机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BEV&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>是否成功</th><th>定性分析</th>
  </tr>
  <tr>
    <td> 7 </td><td> TCP-traj </td> <td>ParkedObstacle</td><td><img src="./gifs/25318_tcp_rgb_front_ParkedObstacle_failed.gif"></td><td><img src="./gifs/25318_tcp_bev_ParkedObstacle_failed.gif"></td> <td> x </td><td>自车尝试避让停放车辆，但由于规划不准确且不稳定，仍与其相撞。</td>
  </tr>  <tr>
    <td> 8</td><td>  UniAD-Base </td> <td>ParkedObstacle</td><td><img src="./gifs/25318_uniad_rgb_front_ParkedObstacle_failed.gif"></td><td><img src="./gifs/25318_uniad_bev_ParkedObstacle_failed.gif"></td><td> x </td><td>自车检测到停放车辆，但轨迹预测错误，最终与其相撞。</td>
  </tr>
  <tr>
    <td> 9 </td><td>  VAD-Base </td> <td>ParkedObstacle</td><td><img src="./gifs/25318_vad_rgb_front_ParkedObstacle_success.gif"></td><td><img src="./gifs/25318_vad_bev_ParkedObstacle_success.gif"></td><td> √ </td><td>自车检测到停放车辆并向左避让，同时避开后方来车。</td>
  </tr>
  <tr>
    <td> 10 </td><td>  TCP-traj </td> <td>HazardAtSideLane</td><td><img src="./gifs/25439_tcp_rgb_front_HazardAtSideLane_failed.gif"></td><td><img src="./gifs/25439_tcp_bev_HazardAtSideLane_failed.gif"></td> <td> x </td><td>自车行为异常，驶上人行道并与骑行者相撞（视频为 2 倍速）。</td>
  </tr>  
  <tr>
    <td> 11 </td><td>  UniAD-Base </td> <td>HazardAtSideLane</td><td><img src="./gifs/25439_uniad_rgb_front_HazardAtSideLane_success.gif"></td><td><img src="./gifs/25439_uniad_bev_HazardAtSideLane_success.gif"></td><td> √ </td><td>自车检测到骑行者，并平稳向左变道。</td>
  </tr>
  <tr>
    <td> 12 </td><td>  VAD-Base </td> <td>HazardAtSideLane</td><td><img src="./gifs/25439_vad_rgb_front_HazardAtSideLane_success.gif"></td><td><img src="./gifs/25439_vad_bev_HazardAtSideLane_success.gif"></td><td> √ </td><td>自车检测到骑行者，减速跟随一段时间后，在不变道的情况下从车道左侧超越。</td>
  </tr>

</table>

# 紧急制动

我们通过三个模型在 `ParkingCutIn` 和 `StaticCutIn` 场景中的行为，展示其紧急制动能力。在这些场景中，自车必须减速或制动，为切入车辆让出空间。

<table>
  <tr>
    <th>案例 ID</th><th>模型</th> <th>场景</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;前视相机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BEV&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>是否成功</th><th>定性分析</th>
  </tr>
  <tr>
    <td> 13 </td><td> TCP-traj </td> <td>ParkingCutIn</td><td><img src="./gifs/18305_tcp_rgb_front_ParkingCutIn_success.gif"></td><td><img src="./gifs/18305_tcp_bev_ParkingCutIn_success.gif"></td> <td> √ </td><td>自车制动并等待停放车辆驶出。</td>
  </tr>  <tr>
    <td> 14 </td><td>  UniAD-Base </td> <td>ParkingCutIn</td><td><img src="./gifs/18305_uniad_rgb_front_ParkingCutIn_success.gif"></td><td><img src="./gifs/18305_uniad_bev_ParkingCutIn_success.gif"></td><td> √ </td><td>自车检测到停放车辆并正确预测其运动，因此制动并等待该车辆驶出。</td>
  </tr>
  <tr>
    <td> 15 </td><td>  VAD-Base </td> <td>ParkingCutIn</td><td><img src="./gifs/18305_vad_rgb_front_ParkingCutIn_failed.gif"></td><td><img src="./gifs/18305_vad_bev_ParkingCutIn_failed.gif"></td><td> x </td><td>自车检测到停放车辆但没有停车，导致连续碰撞。</td>
  </tr>
  <tr>
    <td> 16 </td><td>  TCP-traj </td> <td>StaticCutIn</td><td><img src="./gifs/26396_tcp_rgb_front_StaticCutIn_failed.gif"></td><td><img src="./gifs/26396_tcp_bev_StaticCutIn_failed.gif"></td> <td> x </td><td>自车低速行驶。当右前方车辆试图变道时，自车进行了不必要的左转，导致碰撞。</td>
  </tr>  
  <tr>
    <td> 17 </td><td>  UniAD-Base </td> <td>StaticCutIn</td><td><img src="./gifs/26396_uniad_rgb_front_StaticCutIn_success.gif"></td><td><img src="./gifs/26396_uniad_bev_StaticCutIn_success.gif"></td><td> √ </td><td>其他车辆切入时，自车及时制动。</td>
  </tr>
  <tr>
    <td> 18 </td><td>  VAD-Base </td> <td>StaticCutIn</td><td><img src="./gifs/26396_vad_rgb_front_StaticCutIn_success.gif"></td><td><img src="./gifs/26396_vad_bev_StaticCutIn_success.gif"></td><td> √ </td><td>自车会在其他车辆可能切入的多个位置停车。</td>
  </tr>

</table>

# 让行

我们通过三个模型在 `YieldToEmergencyVehicle` 和 `InvadingTurn` 场景中的行为，展示其让行能力。在 `YieldToEmergencyVehicle` 中，自车必须进行避让操作，让后方应急车辆通过。在 `InvadingTurn` 中，对向来车侵入自车车道，迫使自车向右移动以避免潜在碰撞。

<table>
  <tr>
    <th>案例 ID</th><th>模型</th> <th>场景</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;前视/后视相机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BEV&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>是否成功</th><th>定性分析</th>
  </tr>
  <tr>
    <td> 19 </td><td> TCP-traj </td> <td>YieldTo<br>Emergency<br>Vehicle</td><td><img src="./gifs/3378_tcp_rgb_front_YieldToEmergencyVehicle_failed.gif"><br><img src="./gifs/3378_tcp_rgb_back_YieldToEmergencyVehicle_failed.gif"></td><td><img src="./gifs/3378_tcp_bev_YieldToEmergencyVehicle_failed.gif"></td> <td> x </td><td>TCP 模型不使用后视相机，因此自车无法检测到后方应急车辆。</td>
  </tr>  <tr>
    <td> 20 </td><td>  UniAD-Base </td> <td>YieldTo<br>Emergency<br>Vehicle</td><td><img src="./gifs/3378_uniad_rgb_front_YieldToEmergencyVehicle_failed.gif"><br><img src="./gifs/3378_uniad_rgb_back_YieldToEmergencyVehicle_failed.gif"></td><td><img src="./gifs/3378_uniad_bev_YieldToEmergencyVehicle_failed.gif"></td><td> x </td><td>自车未能检测到应急车辆，也没有进行让行。</td>
  </tr>
  <tr>
    <td> 21 </td><td>  VAD-Base </td> <td>YieldTo<br>Emergency<br>Vehicle</td><td><img src="./gifs/3378_vad_rgb_front_YieldToEmergencyVehicle_failed.gif"><br><img src="./gifs/3378_vad_rgb_back_YieldToEmergencyVehicle_failed.gif"></td><td><img src="./gifs/3378_vad_bev_YieldToEmergencyVehicle_failed.gif"></td><td> x </td><td>自车检测到应急车辆并尝试向右让行，但与右侧车道车辆相撞。</td>
  </tr>
  <tr>
    <td> 22 </td><td>  TCP-traj </td> <td>InvadingTurn</td><td><img src="./gifs/2802_tcp_rgb_front_InvadingTurn_success.gif"></td><td><img src="./gifs/2802_tcp_bev_InvadingTurn_success.gif"></td> <td> √ </td><td>自车低速行驶并向右移动，从而避免碰撞。</td>
  </tr>  
  <tr>
    <td> 23 </td><td>  UniAD-Base </td> <td>InvadingTurn</td><td><img src="./gifs/2802_uniad_rgb_front_InvadingTurn_success.gif"></td><td><img src="./gifs/2802_uniad_bev_InvadingTurn_success.gif"></td><td> √ </td><td>自车以正常速度行驶并向右移动，从而避免碰撞。</td>
  </tr>
  <tr>
    <td> 24 </td><td>  VAD-Base </td> <td>InvadingTurn</td><td><img src="./gifs/2802_vad_rgb_front_InvadingTurn_failed.gif"></td><td><img src="./gifs/2802_vad_bev_InvadingTurn_failed.gif"></td><td> x </td><td>自车移动幅度过大，侵入右侧车道并与其他车辆相撞。</td>
  </tr>

</table>

# 交通标志

我们通过三个模型在 `EnterActorFlow` 和 `VanillaNonSignalizedTurnEncounterStopsign` 场景中的行为，展示其遵守交通标志的能力。在 `EnterActorFlow` 中，自车应遵守交通信号灯；在 `VanillaNonSignalizedTurnEncounterStopsign` 中，自车应在停车标志处停车后再起步。

<table>
  <tr>
    <th>案例 ID</th><th>模型</th> <th>场景</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;前视相机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BEV&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th>是否成功</th><th>定性分析</th>
  </tr>
  <tr>
    <td> 25 </td><td> TCP-traj </td> <td>EnterActorFlow</td><td><img src="./gifs/3749_tcp_rgb_front_EnterActorFlow_success.gif"></td><td><img src="./gifs/3749_tcp_bev_EnterActorFlow_success.gif"></td> <td> √ </td><td>自车遵守交通信号灯并通过路口。</td>
  </tr>  <tr>
    <td> 26 </td><td>  UniAD-Base </td> <td>EnterActorFlow</td><td><img src="./gifs/3749_uniad_rgb_front_EnterActorFlow_failed.gif"></td><td><img src="./gifs/3749_uniad_bev_EnterActorFlow_failed.gif"></td><td> x </td><td>自车检测到交通信号灯，但仍闯红灯。</td>
  </tr>
  <tr>
    <td> 27 </td><td>  VAD-Base </td> <td>EnterActorFlow</td><td><img src="./gifs/3749_vad_rgb_front_EnterActorFlow_failed.gif"></td><td><img src="./gifs/3749_vad_bev_EnterActorFlow_failed.gif"></td><td>x </td><td>自车未能准确检测交通信号灯，并闯红灯。</td>
  </tr>
  <tr>
    <td> 28 </td><td>  TCP-traj </td> <td>Vanilla<br>NonSignalized<br>TurnEncounter<br>Stopsign</td><td><img src="./gifs/3905_tcp_rgb_front_VanillaNonSignalizedTurnEncounterStopsign_success.gif"></td><td><img src="./gifs/3905_tcp_bev_VanillaNonSignalizedTurnEncounterStopsign_success.gif"></td> <td> √ </td><td>自车在停车标志处停车等待，对向车辆通过路口后再驶过路口。</td>
  </tr>  
  <tr>
    <td> 29 </td><td>  UniAD-Base </td> <td>Vanilla<br>NonSignalized<br>TurnEncounter<br>Stopsign</td><td><img src="./gifs/3905_uniad_rgb_front_VanillaNonSignalizedTurnEncounterStopsign_failed.gif"></td><td><img src="./gifs/3905_uniad_bev_VanillaNonSignalizedTurnEncounterStopsign_failed.gif"></td><td> x </td><td>自车没有停车，直接驶过停车标志。</td>
  </tr>
  <tr>
    <td> 30 </td><td>  VAD-Base </td> <td>Vanilla<br>NonSignalized<br>TurnEncounter<br>Stopsign</td><td><img src="./gifs/3905_vad_rgb_front_VanillaNonSignalizedTurnEncounterStopsign_failed.gif"></td><td><img src="./gifs/3905_vad_bev_VanillaNonSignalizedTurnEncounterStopsign_failed.gif"></td><td> x </td><td>自车在停车标志处停车后陷入阻塞，未能再次起步。</td>
  </tr>

</table>

# 结论

- **策略：** 三种 E2E-AD 模型采用了不同策略。TCP 模型较为保守，倾向于以较低速度行驶，以增强避障能力和对突发事件的响应，但可能牺牲通行效率。VAD 模型则采用更激进的策略，增加了车速过快和突然操作的风险，可能导致碰撞。UniAD 的策略介于两者之间。

- **相同场景下的多样化行为：** 值得注意的是，在案例 `10`、`11` 和 `12` 等场景中，使用同一数据集训练的不同模型表现出不同的行为方式，其中可能有多种合理方案，如案例 `11` 和 `12` 所示。
- **感知与规划：** 感知和规划之间的协同至关重要。模型未能检测到附近车辆时，往往会产生错误的路径规划，如案例 `5` 所示。然而，即使目标检测准确，也不一定能保证规划决策正确，如案例 `10` 所示。
- **失败案例分析：** 观察到的失败由多种因素造成，包括无法感知其他车辆（案例 `5` 和 `20`）、运动预测不准确（案例 `8`）、操作幅度过小（案例 `7`）或过大（案例 `24`），以及对场景理解错误（案例 `29` 和 `30`）。
