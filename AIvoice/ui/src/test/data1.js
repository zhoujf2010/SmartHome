var data = {
    // 意图列表
    // 'intentions': [{
    //     'intent': '打招呼'
    // }, {
    //     'intent': '疑问'
    // }],
    // 'intentions': [{
    //     'id': 'H',
    //     'text': '打招呼'
    // }, {
    //     'id': 'Q',
    //     'text': '疑问'
    // }],
    intentions: {
        'H': [{
            id: 'H1',
            text: 'H类型1'
        }, {
            id: 'H2',
            text: 'H类型3'
        }, {
            id: 'H3',
            text: 'H类型3'
        }],
        'Q': [{
            id: 'Q1',
            text: '疑问类型疑问类型疑问类型疑问类型1'
        }, {
            id: 'Q2',
            text: '疑问类型3'
        }, {
            id: 'Q3',
            text: '疑问类型3'
        }],
        'A': [{
            id: 'A1',
            text: '回答类型1'
        }, {
            id: 'A2',
            text: '回答类型3'
        }, {
            id: 'A3',
            text: '回答类型3'
        }]
    },
    // entity 类型列表
    entityTypes: [{
        id: 'time',
        text: '时间',
        bg: '#3391e5'
    }, {
        id: 'food',
        text: '食物',
        bg: '#58cece'
    }, {
        id: 'location',
        text: '地名',
        bg: '#f16caa'
    }, {
        id: 'weather',
        text: '天气',
        bg: '#7d9459'
    }, {
        id: 'hi',
        text: '打招呼',
        bg: '#298aae'
    }],
    // 消息列表
    'messages': [{
        intent: 'Q1',
        'calltype': 'Q',
        'message': '速度花生地',
        // 已经存在（或新增）的实体列表
        entities: [{
            entity: 'time', // 下拉框已选id 时间、地点等等
            start: 0, // 选中实体的开始位置
            length: 2, // 选中实体的文本长度
            end: 2, // 选中实体的结束位置
            value: '速度' // 选中文本内容
        }, {
            entity: 'food',
            start: 2,
            length: 2,
            end: 4,
            value: '花生'
        }, {
            entity: 'location',
            start: 4,
            length: 1,
            end: 5,
            value: '地'
        }]
    }, {
        intent: 'A2',
        'calltype': 'A',
        'message': '钱老师你好',
        entities: [{
            entity: 'hi',
            start: 3,
            length: 2,
            end: 5,
            value: '你好'
        }]
    }, {
        'calltype': 'Q',
        'message': '今天天气怎么样？'
    }, {
        'calltype': 'A',
        'message': '阿斯顿撒奥所多撒奥所多撒所多撒所大所多撒所多撒所大所大所大所大所大所大所'
    }, {
        'calltype': 'Q',
        'message': '请问这是什么啊？这个是一个比较长比较长比较长的问题问题问题'
    }, {
        'calltype': 'A',
        'message': 'sdsfds'
    }, {
        'calltype': 'Q',
        'message': '是否'
    }, {
        'calltype': 'Q',
        'message': '好多爱德华而爱的发把我百度Hi欧'
    }, {
        'calltype': 'Q',
        'message': '是的、'
    }, {
        'calltype': 'Q',
        'message': '房合法化'
    }, {
        'calltype': 'Q',
        'message': 'sd是的'
    }, {
        'calltype': 'Q',
        'message': '123'
    }, {
        'calltype': 'Q',
        'message': '山东黄金'
    }, {
        'calltype': 'Q',
        'message': 'sd'
    }, {
        'calltype': 'Q',
        'message': '你好'
    }, {
        'calltype': 'Q',
        'message': '都好快h'
    }, {
        'calltype': 'Q',
        'message': '546'
    }, {
        'calltype': 'A',
        'message': '奥术大师多阿达大神答案是多xasda'
    }, {
        'calltype': 'Q',
        'message': 'dasdasd'
    }, {
        'calltype': 'Q',
        'message': '我我我我'
    }, {
        'calltype': 'A',
        'message': '我我我我我哦我'
    }, {
        'calltype': 'Q',
        'message': 'XZDSFF'
    }]
}

export const mockData = data;