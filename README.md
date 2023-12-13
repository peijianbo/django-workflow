# django-workflow

基于Django+DRF实现的一个workflow工作流引擎代码示例,支持多级审批，支持或签/会签，支持条件分支。这个项目想传递的价值是模型设计思想，而并不提供完整的API接口和细节处理。


view中有两个主要api：

api/v1/workflow/workflow_nodes/{workflow_node_id}/approve/     --审批通过


api/v1/workflow/workflow_nodes/{workflow_node_id}/approve/     --审批驳回


邮件提醒通过django信号方式：详见 apps/workflow/signals.py




# 模型解释: 

## user app：
    User: 用户表。继承自django的AbstractUser
    Department: 部门表。


## workflow app:
    Field：
        工作流字段表。用于保存某个工作流的必要字段。如一个请假工作流，会包含请假开始时间、结束时间，就可以在这个表中创建
        f1 = Field(name='start_time', label='开始时间') f2 = Field(name='end_time', label='结束时间')

    Workflow: 
        工作流表。如请假/报销/服务器申请。这个表相对简单，主要记录工作流名称。与Field表多对多关系，即每个工作流都会关联一些特殊字段。

    WorkflowChain： 
        工作流程审批链。每个工作流（Workflow）下都关联一个完整的工作流程链。如一个请假工作流的流程审批链：部门部长-->HRBP-->人事专员-->CEO
    
    WorkflowEvent：
        工作流事件。由员工发起。如一个具体的请假/报销/办公用品申请。
    
    WorkflowNode： 
        具体的审批节点。申请人提交申请事件后，根据WorkflowChain定义的工作流程审批链，将具体审批节点拆解到此表。


## 整体运转流程：

    管理员侧：
    1、先由管理员配置好常用的字段（维护Field表），比如请假工作流必要的开始时间/结束时间，报销工作流必要的发票信息/报销金额。
    2、然后由管理员创建工作流（维护Workflow表），比如创建 员工请假、发票报销、办公用品申请等工作流，并且与Field表字段进行关联。
    3、再由管理员预设好工作流程审批链（维护WorkflowChain表），比如给第二步创建的员工请假工作流配置审批链：部门领导-->HRBP-->人事专员-->人事部领导-->CEO，
       注意这个审批链是抽象的且通用的，无论哪个员工请假，都会使用这个审批链。

    员工侧：
    4、以上配置完成，员工就可以提交申请事件了（维护WorkflowEvent表），如提一个请假申请。
    5、步骤4提交申请后，系统会根据管理员配置的`员工请假`工作流程链，自动创建审批节点（维护WorkflowNode表），会根据审批链的审批类型（如部门领导/角色）自动获取审对应批人。
    6、审批节点表WorkflowNode数据有了之后，就可以逐级审批了。


## 高逼格的Field表
    这张表将每个工作流的特有字段提取出来独立存储，而不像那些常规做法把所有信息存到JSONField字段中。这样做的好处是可维护、扩展性强，代码逼格也更高。
    并且通过动态创建序列化器的方式，可以自动反序列化并对字段进行校验（详见to_serializer_field和generate_serializer函数）
