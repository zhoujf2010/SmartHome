(function() {
  var intentions = {
    H: [
      {
        id: "H1",
        text: "H类型1"
      },
      {
        id: "H2",
        text: "H类型2"
      },
      {
        id: "H3",
        text: "H类型3"
      }
    ],
    Q: [
      {
        id: "Q1",
        text: "疑问类型疑问类型疑问类型疑问类型1"
      },
      {
        id: "Q2",
        text: "疑问类型2"
      },
      {
        id: "Q3",
        text: "疑问类型3"
      }
    ],
    A: [
      {
        id: "A1",
        text: "回答类型1"
      },
      {
        id: "A2",
        text: "回答类型2"
      },
      {
        id: "A3",
        text: "回答类型3"
      }
    ]
  };

  var entityTypes = [
    {
      id: "time",
      text: "时间",
      bg: "#3391e5"
    },
    {
      id: "food",
      text: "食物",
      bg: "#58cece"
    },
    {
      id: "location",
      text: "地名",
      bg: "#f16caa"
    },
    {
      id: "weather",
      text: "天气",
      bg: "#7d9459"
    },
    {
      id: "hi",
      text: "打招呼",
      bg: "#298aae"
    }
  ];

  var entityTypeLen = entityTypes.length - 1;
  var list = Mock.mock({
    "list|6-20": [
      {
        message: "@csentence(200,2000)"
      }
    ]
  }).list;

  list.forEach(function(item, i) {
    var isOdd = i % 2 !== 0;
    item.intent = (isOdd ? "A" : "Q") + Mock.mock("@integer(1,3)");
    item.calltype = isOdd ? "A" : "Q";

    var len = Mock.Random.integer(0, 2);
    if (len) {
      item.entities = [];
      new Array(len).forEach(function() {
        var s = Mock.Random.integer(0, item.message.length - 10);
        var l = Mock.Random.integer(1, 9);
        var e = s + l;

        item.entities.push({
          entity: entityTypes[Mock.Random.integer(0, entityTypeLen - 1)].id,
          start: s,
          length: l,
          end: e,
          value: item.message.substring(s, e)
        });
      });
    }
  });

  window.mockData = {
    intentions: intentions,
    entityTypes: entityTypes,
    messages: list,
    messageTypeList: [
      {
        id: "类型1",
        text: "类型1"
      },
      {
        id: "类型2",
        text: "类型2"
      },
      {
        id: "类型3",
        text: "类型3"
      }
    ]
  };
})();
